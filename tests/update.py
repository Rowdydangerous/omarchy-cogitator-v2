#!/usr/bin/env python3
"""Offline update fixtures: real local Git repositories, never the live desktop."""
import fcntl
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
Updater = runpy.run_path(str(ROOT / "scripts/update-source.py"))["Updater"]


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.author = self.work / "author"
        self.author.mkdir()
        self.git("init", "--quiet", "--initial-branch=main", str(self.author))
        (self.author / "scripts").mkdir()
        (self.author / "scripts/cogitator").write_text("#!/bin/bash\nexit 0\n")
        self.commit("initial")
        self.updater = Updater(ROOT, self.work / "data", self.work / "state/cogitator-v2",
                               self.work / "config", str(self.author))

    def git(self, *args, cwd=None):
        return subprocess.check_output(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", *args],
                                       cwd=cwd, text=True, stderr=subprocess.PIPE).strip()

    def commit(self, message):
        self.git("add", "-A", cwd=self.author)
        self.git("commit", "--quiet", "-m", message, cwd=self.author)

    def test_clone_fast_forward_and_unrelated_untracked_file_preserved(self):
        first = self.updater.prepare_source()
        local = self.updater.source / "user-notes.txt"
        local.write_text("keep me")
        (self.author / "new.txt").write_text("release two")
        self.commit("second")
        second = self.updater.prepare_source()
        self.assertNotEqual(first, second)
        self.assertEqual(local.read_text(), "keep me")
        self.assertEqual((self.updater.source / "new.txt").read_text(), "release two")

    def test_tracked_local_edits_are_not_discarded(self):
        self.updater.prepare_source()
        file = self.updater.source / "scripts/cogitator"
        file.write_text("USER EDIT")
        with self.assertRaisesRegex(RuntimeError, "local tracked changes"):
            self.updater.prepare_source()
        self.assertEqual(file.read_text(), "USER EDIT")

    def test_foreign_source_is_not_overwritten(self):
        self.updater.source.mkdir(parents=True)
        file = self.updater.source / "original"
        file.write_text("user")
        with self.assertRaisesRegex(RuntimeError, "not managed"):
            self.updater.prepare_source()
        self.assertEqual(file.read_text(), "user")

    def test_local_commits_are_not_treated_as_a_published_update(self):
        self.updater.prepare_source()
        (self.updater.source / "local.txt").write_text("USER COMMIT")
        self.git("add", "local.txt", cwd=self.updater.source)
        self.git("commit", "--quiet", "-m", "local change", cwd=self.updater.source)
        before = self.git("rev-parse", "HEAD", cwd=self.updater.source)
        with self.assertRaisesRegex(RuntimeError, "local commits"):
            self.updater.prepare_source()
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=self.updater.source), before)

    def test_untracked_collision_stops_merge_without_discard(self):
        first = self.updater.prepare_source()
        (self.updater.source / "new.txt").write_text("USER FILE")
        (self.author / "new.txt").write_text("UPSTREAM FILE")
        self.commit("collision")
        with self.assertRaises(subprocess.CalledProcessError):
            self.updater.prepare_source()
        self.assertEqual((self.updater.source / "new.txt").read_text(), "USER FILE")
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=self.updater.source), first)

    def test_deploy_preserves_mode_and_uses_downloaded_source(self):
        with patch("subprocess.run") as run:
            self.updater.deploy()
            self.assertEqual(run.call_args.args[0][-1], "install")
            self.updater.state.mkdir(parents=True)
            (self.updater.state / "snapshot.json").write_text("{\"previousTheme\":\"original\"}")
            self.updater.deploy()
            self.assertEqual(run.call_args.args[0][-1], "apply")
            self.assertEqual(run.call_args.args[0][1], str(self.updater.source / "scripts/cogitator"))

    def test_update_backs_up_settings_and_retains_failure_evidence(self):
        file = self.updater.config / "cogitator-v2/cogitator.conf"
        file.parent.mkdir(parents=True)
        file.write_text('PALETTE="amber"\n# USER COMMENT\n')
        with patch.object(self.updater, "preflight"), patch.object(self.updater, "validate"), \
             patch.object(self.updater, "deploy", side_effect=RuntimeError("fixture failure")):
            with self.assertRaisesRegex(RuntimeError, "fixture failure"):
                self.updater.update()
        record_path = next((self.updater.state / "backups").glob("update-*/update.json"))
        self.assertEqual(json.loads(record_path.read_text())["phase"], "failed")
        self.assertEqual((record_path.parent / "cogitator.conf").read_bytes(), file.read_bytes())

    def test_inactive_native_install_does_not_leave_coordinator_running(self):
        (self.updater.config / "omarchy/plugins/cogitator-rite").mkdir(parents=True)
        with patch("subprocess.run") as run:
            self.updater.deploy()
        self.assertEqual(run.call_args_list[0].args[0], ["omarchy", "plugin", "disable", "cogitator-rite"])
        self.assertEqual(run.call_args_list[1].args[0][-1], "install")

    def test_concurrent_update_refused(self):
        self.updater.state.mkdir(parents=True)
        with (self.updater.state / "update.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(RuntimeError, "Another Cogitator update"):
                self.updater.update()

    def test_runtime_qml_edits_refused_before_source_update(self):
        core = self.updater.config / "omarchy/plugins/cogitator-rite"
        (core / "qml").mkdir(parents=True)
        (core / ".cogitator-v2-installed").write_text("owned")
        (core / "qml/Service.qml").write_text("USER EDIT")
        (core / ".cogitator-runtime.json").write_text('{"files":{}}')
        with self.assertRaisesRegex(RuntimeError, "local QML edits"):
            self.updater.update()
        self.assertFalse(self.updater.source.exists())
        self.assertEqual((core / "qml/Service.qml").read_text(), "USER EDIT")


if __name__ == "__main__":
    unittest.main()
