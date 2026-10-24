#!/usr/bin/env python3
"""Update from GitHub through a dedicated source checkout, not runtime clones."""
import fcntl
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/Rowdydangerous/omarchy-cogitator-v2.git"


class Updater:
    def __init__(self, root=ROOT, data=None, state=None, config=None, repository=REPOSITORY):
        self.root = Path(root)
        self.data = Path(data or Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "cogitator-v2")
        self.state = Path(state or Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "cogitator-v2")
        self.config = Path(config or os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        self.repository = repository
        self.source = self.data / "source"
        self.receipt = self.data / "update-source.json"
        self.env = dict(os.environ, GIT_TERMINAL_PROMPT="0", COGITATOR_FOREGROUND="1",
                        OMARCHY_PATH=os.environ.get("OMARCHY_PATH", "/usr/share/omarchy"))

    def git(self, *args, cwd=None):
        return subprocess.check_output(["git", *args], cwd=cwd, env=self.env, text=True).strip()

    def prepare_source(self):
        self.data.mkdir(parents=True, exist_ok=True)
        if self.source.is_symlink():
            raise RuntimeError(f"Update source is a symlink; preserved: {self.source}")
        if self.source.exists():
            if not self.receipt.is_file() or not (self.source / ".git").is_dir():
                raise RuntimeError(f"Update source is not managed; preserved: {self.source}")
            receipt = json.loads(self.receipt.read_text())
            if receipt.get("repository") != self.repository or self.git("remote", "get-url", "origin", cwd=self.source) != self.repository:
                raise RuntimeError("Update source has a different origin; preserved")
            if self.git("status", "--porcelain", "--untracked-files=no", cwd=self.source):
                raise RuntimeError("Update source has local tracked changes; preserved. Inspect " + str(self.source))
            if self.git("branch", "--show-current", cwd=self.source) != "main":
                raise RuntimeError("Update source is not on main; preserved")
            self.git("fetch", "--quiet", "origin", "main", cwd=self.source)
            try:
                self.git("merge-base", "--is-ancestor", "HEAD", "FETCH_HEAD", cwd=self.source)
            except subprocess.CalledProcessError:
                raise RuntimeError("Update source has local commits or a diverged branch; preserved")
            # Git refuses diverged branches and conflicting untracked files;
            # never reset, clean, stash, or discard user work automatically.
            self.git("merge", "--ff-only", "FETCH_HEAD", cwd=self.source)
        else:
            stage = Path(tempfile.mkdtemp(prefix=".update-", dir=self.data))
            try:
                self.git("clone", "--quiet", "--branch", "main", "--single-branch", self.repository, str(stage))
                if not (stage / "scripts/cogitator").is_file():
                    raise RuntimeError("Downloaded source is missing scripts/cogitator")
                stage.rename(self.source)
                self.receipt.write_text(json.dumps({"repository": self.repository}) + "\n")
            finally:
                if stage.exists():
                    shutil.rmtree(stage)
        return self.git("rev-parse", "HEAD", cwd=self.source)

    def preflight(self):
        api = runpy.run_path(str(self.root / "scripts/cogitator-suite.py"))
        suite = api["Suite"](self.root, self.config, self.state.parent)
        suite.preflight()
        core = suite.plugins / "cogitator-rite"
        if core.exists():
            if core.is_symlink():
                raise RuntimeError("Coordinator is not a managed installation; preserved")
            if not (core / ".cogitator-v2-installed").is_file():
                if not (core / ".git").is_dir() or self.git("remote", "get-url", "origin", cwd=core).removesuffix(".git") != self.repository.removesuffix(".git"):
                    raise RuntimeError("Coordinator is not a managed installation; preserved")
            receipt = core / ".cogitator-runtime.json"
            if receipt.exists():
                if json.loads(receipt.read_text())["files"] != api["file_hashes"](core / "qml"):
                    raise RuntimeError("Coordinator has local QML edits; preserved")
            elif self.git("status", "--porcelain", "--", "qml", cwd=core):
                raise RuntimeError("Coordinator has unreceipted QML edits; preserved")

    def deploy(self):
        # apply keeps the active palette/wallpaper and the restore journals;
        # inactive installs update the controller without engaging the suite.
        active = (self.state / "snapshot.json").exists() or (self.state / "suite.json").exists()
        command = "apply" if active else "install"
        if not active and (self.config / "omarchy/plugins/cogitator-rite").exists():
            # Native plugin add can enable the service before any suite journal
            # exists. Do not leave its Node/OSD active after an inactive update.
            subprocess.run(["omarchy", "plugin", "disable", "cogitator-rite"], env=self.env, check=True)
        subprocess.run(["bash", str(self.source / "scripts/cogitator"), command], env=self.env, check=True)

    def validate(self):
        subprocess.run(["omarchy", "plugin", "validate", str(self.source)], env=self.env, check=True)

    def update(self):
        self.state.mkdir(parents=True, exist_ok=True)
        with (self.state / "update.lock").open("w") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError("Another Cogitator update is running")
            self.preflight()
            previous_commit = self.git("rev-parse", "HEAD", cwd=self.source) if (self.source / ".git").is_dir() else None
            commit = self.prepare_source()
            backup = self.state / "backups" / f"update-{time.time_ns()}"
            backup.mkdir(parents=True)
            for source, name in ((self.config / "cogitator-v2/cogitator.conf", "cogitator.conf"),
                                 (self.config / "omarchy/shell.json", "shell.json"),
                                 (self.state / "snapshot.json", "snapshot.json"),
                                 (self.state / "suite.json", "suite.json")):
                if source.is_file():
                    shutil.copy2(source, backup / name)
            record = {"commit": commit, "previousSource": str(self.root), "source": str(self.source),
                      "previousCommit": previous_commit, "phase": "deploying"}
            record_path = backup / "update.json"
            record_path.write_text(json.dumps(record, indent=2) + "\n")
            try:
                self.validate()
                self.deploy()
            except Exception:
                record["phase"] = "failed"
                raise
            else:
                record["phase"] = "completed"
            finally:
                record_path.write_text(json.dumps(record, indent=2) + "\n")
            print(f"Updated Cogitator from GitHub: {commit[:12]}. Recovery files: {backup}")


if __name__ == "__main__":
    try:
        Updater().update()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"Cogitator update failed: {error}")
