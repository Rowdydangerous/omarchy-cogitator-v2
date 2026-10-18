#!/usr/bin/env python3
"""Meaningful suite routing/installation/rollback fixtures; never touch HOME."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("suite", ROOT / "scripts/cogitator-suite.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def metadata(source, kinds, enabled=True, identity=None):
    return {"id": identity or source, "clonedFrom": source if identity else "",
            "kinds": kinds, "enabled": enabled}


BASELINES = [{"sourceId": "omarchy." + slug, "replacementId": "cogitator." + slug,
              "path": "plugins/" + slug}
             for slug in ("bar", "clock", "indicators", "spacer", "idle", "media")]
CATALOG = [metadata("omarchy.bar", ["bar"]), metadata("omarchy.clock", ["bar-widget"]),
           metadata("omarchy.indicators", ["bar-widget"]), metadata("omarchy.spacer", ["bar-widget"]),
           metadata("omarchy.idle", ["service"], False),
           metadata("omarchy.idle", ["service"], identity="rowdy.idle"),
           metadata("omarchy.media", ["service", "bar-widget"], False)]
CONFIG = {"version": 1, "bar": {"position": "left", "transparent": True,
          "centerAnchor": "omarchy.clock", "layout": {
              "left": [{"id": "omarchy.indicators", "items": ["Dnd"]}, {"id": "omarchy.spacer", "size": 8}],
              "center": [{"id": "omarchy.clock", "format": "HH:mm"},
                         {"id": "omarchy.indicators", "items": ["Reminder"]}],
              "right": [{"id": "omarchy.spacer", "size": 16}, {"id": "unrelated.widget", "color": "blue"}]}},
          "plugins": [{"id": "rowdy.idle", "customSetting": 3}, {"id": "unrelated.service"}],
          "disabledPlugins": ["omarchy.idle", "omarchy.media"], "idle": {"lock": 777}}


class RoutingTests(unittest.TestCase):
    def test_repeated_instances_settings_anchors_and_custom_service(self):
        before = copy.deepcopy(CONFIG)
        after, mapping, selected = module.plan_config(before, CATALOG, BASELINES, True)
        self.assertEqual(before, CONFIG)
        self.assertEqual(after["bar"]["id"], "cogitator.bar")
        self.assertEqual(after["bar"]["centerAnchor"], "cogitator.clock")
        for section in CONFIG["bar"]["layout"]:
            for original, new in zip(CONFIG["bar"]["layout"][section], after["bar"]["layout"][section]):
                self.assertEqual(new, module.remap_entry(original, mapping))
        self.assertEqual(after["plugins"][0], {"id": "cogitator.idle", "customSetting": 3})
        self.assertIn("rowdy.idle", after["disabledPlugins"])
        self.assertNotIn("omarchy.media", mapping)
        self.assertEqual(module.rollback_config(before, after, after), before)

    def test_preserve_engaged_settings_reordering_and_unrelated_edits(self):
        after, _, _ = module.plan_config(CONFIG, CATALOG, BASELINES, True)
        current = copy.deepcopy(after)
        current["idle"]["lock"] = 999
        current["bar"]["position"] = "bottom"
        current["bar"]["layout"]["center"][0]["format"] = "HH:mm:ss"
        current["bar"]["layout"]["left"].reverse()
        current["bar"]["layout"]["right"].append({"id": "cogitator.spacer", "size": 30})
        current["plugins"].append({"id": "new.user.service"})
        current["disabledPlugins"].append("new.user.disabled")
        restored = module.rollback_config(CONFIG, after, current)
        self.assertEqual(restored["bar"]["layout"]["center"][0], {"id": "omarchy.clock", "format": "HH:mm:ss"})
        self.assertEqual(restored["bar"]["layout"]["left"], list(reversed(CONFIG["bar"]["layout"]["left"])))
        self.assertEqual(restored["bar"]["layout"]["right"][-1], {"id": "omarchy.spacer", "size": 30})
        self.assertEqual(restored["bar"]["position"], "bottom")
        self.assertEqual(restored["idle"]["lock"], 999)
        self.assertIn({"id": "new.user.service"}, restored["plugins"])
        self.assertNotIn({"id": "cogitator-rite"}, restored["plugins"])
        self.assertIn("new.user.disabled", restored["disabledPlugins"])

    def test_custom_widget_clones_and_inactive_clones(self):
        config = copy.deepcopy(CONFIG)
        config["bar"]["layout"]["center"][0]["id"] = "rowdy.clock"
        config["bar"]["centerAnchor"] = "rowdy.clock"
        catalog = copy.deepcopy(CATALOG)
        catalog.append(metadata("omarchy.clock", ["bar-widget"], identity="rowdy.clock"))
        catalog.append(metadata("omarchy.clock", ["bar-widget"], False, "other.clock"))
        after, mapping, _ = module.plan_config(config, catalog, BASELINES)
        self.assertEqual(after["bar"]["centerAnchor"], "cogitator.clock")
        self.assertNotIn("other.clock", mapping)
        self.assertEqual(module.rollback_config(config, after, after), config)

    def test_custom_widget_moved_between_sections_restores_original_clone(self):
        config = copy.deepcopy(CONFIG)
        config["bar"]["layout"]["center"][0]["id"] = "rowdy.clock"
        catalog = CATALOG + [metadata("omarchy.clock", ["bar-widget"], identity="rowdy.clock")]
        after, _, _ = module.plan_config(config, catalog, BASELINES)
        current = copy.deepcopy(after)
        clock = current["bar"]["layout"]["center"].pop(0)
        clock["format"] = "changed"
        current["bar"]["layout"]["right"].append(clock)
        restored = module.rollback_config(config, after, current)
        self.assertEqual(restored["bar"]["layout"]["right"][-1], {"id": "rowdy.clock", "format": "changed"})

    def test_ambiguous_edited_instances_keep_journal_instead_of_guessing(self):
        config = copy.deepcopy(CONFIG)
        config["bar"]["layout"]["center"] = [{"id": "rowdy.clock", "format": "A"}, {"id": "other.clock", "format": "B"}]
        catalog = CATALOG + [metadata("omarchy.clock", ["bar-widget"], identity="rowdy.clock"),
                             metadata("omarchy.clock", ["bar-widget"], identity="other.clock")]
        after, _, _ = module.plan_config(config, catalog, BASELINES)
        current = copy.deepcopy(after)
        current["bar"]["layout"]["center"][0]["format"] = "changed"
        with self.assertRaises(RuntimeError):
            module.rollback_config(config, after, current)

    def test_absent_widgets_and_disabled_services_stay_off(self):
        config = {"bar": {"layout": {"left": [], "center": [], "right": []}}, "plugins": [],
                  "disabledPlugins": ["omarchy.idle", "omarchy.media"]}
        catalog = [p for p in CATALOG if p["id"] != "rowdy.idle"]
        _, mapping, _ = module.plan_config(config, catalog, BASELINES)
        self.assertEqual(mapping, {"omarchy.bar": "cogitator.bar"})


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.root = self.work / "repo"
        (self.root / "docs").mkdir(parents=True)
        (self.root / "docs/stock-baseline.json").write_text(json.dumps({"plugins": BASELINES}))
        for plugin in BASELINES:
            directory = self.root / plugin["path"]
            directory.mkdir(parents=True)
            (directory / "Entry.qml").write_text("import QtQuick\nItem {}\n")
            (directory / "manifest.json").write_text(json.dumps({"id": plugin["replacementId"]}))
        self.defaults = self.work / "defaults.json"
        self.defaults.write_text(json.dumps(CONFIG))
        self.calls = []
        self.fail_validation = False

        def run(args):
            self.calls.append(args)
            if args[0] == "git":
                return ""
            if args[:3] == ["omarchy", "plugin", "validate"] and self.fail_validation:
                raise RuntimeError("fixture validation failure")
            if args[-1] == "listPlugins":
                installed = [metadata("omarchy." + p.name.removeprefix("cogitator."), ["bar-widget"], False, p.name)
                             for p in self.suite.plugins.glob("cogitator.*") if (p / "manifest.json").exists()]
                return json.dumps(CATALOG + installed)
            return "ok"

        self.suite = module.Suite(self.root, self.work / "config", self.work / "state", self.defaults, run)

    def test_install_switch_and_exact_restore_preserve_custom_files(self):
        self.suite.config.parent.mkdir(parents=True)
        original = (json.dumps(CONFIG, separators=(",", ":")) + "\n").encode()
        self.suite.config.write_bytes(original)
        self.suite.config.chmod(0o640)
        custom = self.suite.plugins / "rowdy.idle"
        custom.mkdir(parents=True)
        (custom / "custom.qml").write_text("USER ORIGINAL")
        journal = self.suite.prepare(True)
        self.suite.enable()
        self.assertEqual(json.loads(self.suite.config.read_text()), journal["applied"])
        self.assertEqual((custom / "custom.qml").read_text(), "USER ORIGINAL")
        original_journal = self.suite.journal.read_bytes()
        self.suite.prepare(True)
        self.suite.enable()
        self.assertEqual(self.suite.journal.read_bytes(), original_journal)
        self.suite.disable()
        self.assertEqual(self.suite.config.read_bytes(), original)
        self.assertEqual(self.suite.config.stat().st_mode & 0o777, 0o640)
        self.suite.finish()
        self.assertFalse(self.suite.journal.exists())
        self.assertTrue((Path(journal["backup"]) / "suite-journal.json").exists())
        # Retained inactive installs can be reused safely on the next cycle.
        self.suite.prepare(True)
        self.suite.enable()
        self.suite.disable()
        self.suite.finish()
        self.assertEqual(self.suite.config.read_bytes(), original)

    def test_absent_config_returns_to_absent(self):
        defaults = self.defaults.read_bytes()
        self.suite.prepare()
        self.suite.enable()
        self.suite.disable()
        self.assertFalse(self.suite.config.exists())
        self.assertEqual(self.defaults.read_bytes(), defaults)

    def test_foreign_collision_preserved_and_no_switch(self):
        target = self.suite.plugins / "cogitator.clock"
        target.mkdir(parents=True)
        (target / "user.txt").write_text("DO NOT TOUCH")
        self.suite.prepare()
        with self.assertRaises(RuntimeError):
            self.suite.enable()
        self.assertFalse(self.suite.config.exists())
        self.assertEqual((target / "user.txt").read_text(), "DO NOT TOUCH")
        self.suite.disable()
        self.suite.finish()

    def test_validation_failure_keeps_recovery_and_config(self):
        self.suite.prepare()
        self.fail_validation = True
        with self.assertRaises(RuntimeError):
            self.suite.enable()
        self.assertTrue(self.suite.journal.exists())
        self.assertFalse(self.suite.config.exists())
        self.suite.disable()
        self.suite.finish()

    def test_edited_managed_install_not_overwritten(self):
        self.suite.prepare()
        self.suite.enable()
        self.suite.disable()
        self.suite.finish()
        target = self.suite.plugins / "cogitator.clock/Entry.qml"
        target.write_text("USER EDIT")
        self.suite.prepare()
        with self.assertRaises(RuntimeError):
            self.suite.enable()
        self.assertEqual(target.read_text(), "USER EDIT")

    def test_coordinator_refresh_backs_up_and_preserves_direct_edits(self):
        source = self.root / "qml"
        source.mkdir()
        (source / "Service.qml").write_text("NEW WORKING TREE")
        core = self.suite.plugins / "cogitator-rite"
        (core / "qml").mkdir(parents=True)
        (core / ".cogitator-v2-installed").write_text("owned")
        (core / "qml/Service.qml").write_text("OLD NATIVE CODE")
        journal = self.suite.prepare(True)
        self.suite.enable()
        self.assertEqual((core / "qml/Service.qml").read_text(), "NEW WORKING TREE")
        backups = list(Path(journal["backup"]).glob("coordinator-qml-*"))
        self.assertEqual((backups[0] / "Service.qml").read_text(), "OLD NATIVE CODE")
        (core / "qml/Service.qml").write_text("USER EDIT")
        with self.assertRaises(RuntimeError):
            self.suite.refresh()
        self.assertEqual((core / "qml/Service.qml").read_text(), "USER EDIT")

    def test_interrupted_atomic_switch_can_restore(self):
        journal = self.suite.prepare(True)
        journal["phase"] = "switching"
        self.suite.save(journal)
        module.atomic_write(self.suite.config, module.json_bytes(journal["applied"]))
        self.suite.disable()
        self.assertFalse(self.suite.config.exists())
        self.suite.finish()

    def test_refresh_keeps_identical_plugin_directories(self):
        self.suite.prepare()
        self.suite.enable()
        before = {p.name: p.stat().st_ino for p in self.suite.plugins.iterdir()}
        config = self.suite.config.read_bytes()
        self.suite.refresh()
        after = {p.name: p.stat().st_ino for p in self.suite.plugins.iterdir()}
        self.assertEqual(before, after)
        self.assertEqual(self.suite.config.read_bytes(), config)

    def test_runtime_staging_does_not_write_inside_live_plugin(self):
        source = self.root / "qml"
        source.mkdir()
        (source / "Service.qml").write_text("NEW CODE")
        core = self.suite.plugins / "cogitator-rite"
        (core / "qml").mkdir(parents=True)
        (core / ".cogitator-v2-installed").write_text("owned")
        (core / "qml/Service.qml").write_text("OLD CODE")
        journal = self.suite.prepare(True)
        original = module.tempfile.mkdtemp
        with patch.object(module.tempfile, "mkdtemp", wraps=original) as create:
            self.suite.sync_runtime(journal)
            self.suite.sync_runtime(journal)  # No-op staging must also be ignored.
        calls = [c for c in create.call_args_list if c.kwargs.get("prefix") == ".cogitator-runtime-"]
        self.assertEqual(len(calls), 2)
        for call in calls:
            self.assertEqual(call.kwargs["dir"], self.suite.plugins)
        self.assertFalse(any(p.name.startswith(".cogitator-runtime-") for p in self.suite.plugins.iterdir()))


if __name__ == "__main__":
    unittest.main()
