#!/usr/bin/env python3
"""Persistent placement/rebase, safe settings and controller packaging checks."""
import copy
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
API = runpy.run_path(str(ROOT / "scripts/control-backend.py"))


class SettingsTests(unittest.TestCase):
    def test_palette_names_are_presentation_only(self):
        field = next(field for field in API["SCHEMA"] if field["key"] == "PALETTE")
        self.assertEqual(field["choiceLabels"], {"green": "Imperium", "amber": "Ryza",
                         "red": "Holy Mars", "industrial": "Metalica", "custom": "Custom"})
        self.assertEqual(set(field["choices"]), set(field["choiceLabels"]))
        for identity, label in field["choiceLabels"].items():
            values = {"PALETTE": identity, "CUSTOM_PHOSPHOR": "#abc"}
            self.assertEqual(API["validate"](values)["PALETTE"], identity)
            self.assertIn(f'PALETTE="{identity}"', API["write_settings"]("", values))
            if label != identity:
                with self.assertRaises(ValueError):
                    API["validate"]({"PALETTE": label})

    def test_all_supported_example_settings_are_exposed(self):
        example = API["parse_conf"]((ROOT / "config/cogitator.conf.example").read_text())
        self.assertEqual(set(example), {field["key"] for field in API["SCHEMA"]})

    def test_hex_comments_and_types(self):
        values = API["parse_conf"]('CUSTOM_PHOSPHOR="#7CFF6B" # chosen color\nCRT_GLOBAL=false # disabled\n')
        validated = API["validate"](values)
        self.assertEqual(validated["CUSTOM_PHOSPHOR"], "#7CFF6B")
        self.assertFalse(validated["CRT_GLOBAL"])

    def test_invalid_inputs_rejected(self):
        for payload in ({"CRT_INTENSITY": 5}, {"WINDOW_CORNER": 2.5}, {"FLICKER": float("nan")},
                        {"CRT_GLOBAL": "maybe"}, {"PALETTE": "custom"},
                        {"CUSTOM_PHOSPHOR": "#fff; touch x"}, {"UNKNOWN_SETTING": True}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                API["validate"](payload)

    def test_write_preserves_unknown_settings_and_comment_lines(self):
        raw = '# Operator notes\nOTHER="keep me"\nCRT_GLOBAL=true\nCRT_GLOBAL=true\n'
        updated = API["write_settings"](raw, API["validate"]({"CRT_GLOBAL": False}))
        self.assertIn('# Operator notes\nOTHER="keep me"', updated)
        self.assertEqual(updated.count("CRT_GLOBAL="), 1)
        self.assertEqual(API["parse_conf"](updated)["OTHER"], "keep me")

    def test_old_out_of_range_values_read_as_effective_settings(self):
        raw = 'FLICKER="0.35"\nWINDOW_CORNER="14.5"\n'
        effective = API["settings"](raw)
        self.assertEqual(effective["FLICKER"], 0.3)
        self.assertEqual(effective["WINDOW_CORNER"], 14)
        self.assertEqual(raw, 'FLICKER="0.35"\nWINDOW_CORNER="14.5"\n')

    def test_inactive_save_only_changes_requested_values_and_rejects_conflict(self):
        globals_ = API["queue"].__globals__
        with tempfile.TemporaryDirectory() as work:
            work = Path(work)
            conf = work / "settings.conf"
            raw = '# Keep my notes\nFLICKER="0.35"\nTEXT_STREAMING=true\nOTHER="untouched"\n'
            conf.write_text(raw)
            values = API["settings"](raw)
            values["TEXT_STREAMING"] = False
            payload = {"revision": API["revision"](raw), "values": values, "changed": ["TEXT_STREAMING"]}
            with patch.dict(globals_, {"CONF": conf, "STATE": work / "state", "OPERATION": work / "state/control-operation.json", "status": lambda: {"busy": False, "engaged": False}}):
                result = API["queue"]("apply", payload)
                self.assertTrue(result["ok"])
                self.assertIn('FLICKER="0.35"', conf.read_text())
                self.assertIn('OTHER="untouched"', conf.read_text())
                self.assertIn('TEXT_STREAMING=false', conf.read_text())
                with self.assertRaises(RuntimeError):
                    API["queue"]("apply", payload)


class PlacementTests(unittest.TestCase):
    def test_custom_clock_anchor_and_other_instances_preserved(self):
        config = {"bar": {"centerAnchor": "rowdy.clock", "layout": {
            "left": [{"id": "omarchy.clock", "format": "HH:mm"}],
            "center": [{"id": "rowdy.clock", "format": "HH:mm:ss"}, {"id": "custom.widget"}], "right": []}}}
        catalog = [{"id": "rowdy.clock", "clonedFrom": "omarchy.clock"}]
        result = API["place_control"](config, catalog)
        self.assertEqual(result["bar"]["layout"]["center"][0], {"id": "cogitator.control"})
        self.assertEqual(result["bar"]["layout"]["center"][1], config["bar"]["layout"]["center"][0])
        self.assertEqual(result["bar"]["layout"]["left"], config["bar"]["layout"]["left"])
        self.assertEqual(API["place_control"](result, catalog), result)

    def test_no_clock_fallback_and_existing_placement(self):
        config = {"bar": {"layout": {"left": [], "center": [], "right": [{"id": "other"}]}}}
        result = API["place_control"](config, [])
        self.assertEqual(result["bar"]["layout"]["center"], [{"id": "cogitator.control"}])
        result["bar"]["layout"]["center"] = []
        result["bar"]["layout"]["right"].append({"id": "cogitator.control"})
        self.assertEqual(API["place_control"](result, []), result)

    def test_control_survives_suite_switch_and_rollback(self):
        config = API["place_control"]({"version": 1, "bar": {"layout": {"center": [{"id": "omarchy.clock"}]}}}, [])
        catalog = [{"id": "omarchy.clock", "enabled": True, "kinds": ["bar-widget"], "clonedFrom": ""},
                   {"id": "cogitator.control", "enabled": True, "kinds": ["bar-widget"], "clonedFrom": ""}]
        baselines = [{"sourceId": "omarchy.clock", "replacementId": "cogitator.clock"}]
        applied, mapping, selected = API["SUITE"]["plan_config"](config, catalog, baselines)
        self.assertEqual(applied["bar"]["layout"]["center"], [{"id": "cogitator.control"}, {"id": "cogitator.clock"}])
        self.assertEqual(API["SUITE"]["rollback_config"](config, applied, applied), config)


class PackagingTests(unittest.TestCase):
    def test_control_icon_uses_native_vectors_without_effect_layer(self):
        source = (ROOT / "control/Panel.qml").read_text()
        emblem = (ROOT / "control/CogSkull.qml").read_text()
        self.assertNotIn("import QtQuick.Effects", source)
        self.assertIn("CogSkull { color: root.ink }", source)
        self.assertNotIn("layer.enabled:", source)
        self.assertNotIn("source: Qt.resolvedUrl(\"icons/", source)
        self.assertNotIn("Image {", emblem)
        self.assertNotIn("MultiEffect {", emblem)
        self.assertNotIn("layer.enabled:", emblem)

    def test_controller_manifest_and_qml(self):
        with tempfile.TemporaryDirectory() as work:
            stage = Path(work) / "control"
            shutil.copytree(ROOT / "control", stage)
            shutil.copytree(ROOT / "shared/frames", stage / "frames")
            subprocess.run(["omarchy", "plugin", "validate", str(stage)], check=True, stdout=subprocess.DEVNULL)
            # Quickshell uses Qt 6; /usr/bin/qmllint here is the older Qt 5
            # parser. Host qs.* namespaces are supplied dynamically at runtime.
            subprocess.run(["/usr/lib/qt6/bin/qmllint", "--ignore-settings", "--silent",
                            "-I", "/usr/share/omarchy/shell", str(stage / "Panel.qml"), str(stage / "CogSkull.qml")], check=True)

    def test_active_install_rebases_controller_into_both_sides(self):
        globals_ = API["install_control"].__globals__
        with tempfile.TemporaryDirectory() as work:
            work = Path(work)
            suite = API["SUITE"]["Suite"](ROOT, work / "config", work / "state")
            before = {"version": 1, "plugins": [], "bar": {"layout": {"center": [{"id": "omarchy.clock"}]}}}
            applied = copy.deepcopy(before)
            applied["bar"]["layout"]["center"][0]["id"] = "cogitator.clock"
            suite.config.parent.mkdir(parents=True)
            suite.config.write_text(json.dumps(applied))
            journal = {"before": before, "applied": applied, "catalog": [], "phase": "active"}
            suite.save(journal)
            fake_suite = dict(API["SUITE"], Suite=lambda: suite)
            def check_output(command, **kwargs):
                return json.dumps([{"id": "cogitator.clock", "clonedFrom": "omarchy.clock"}])
            with patch.dict(globals_, {"SUITE": fake_suite, "STATE": suite.state, "OPERATION": suite.state / "control-operation.json"}), \
                 patch("subprocess.run"), patch("subprocess.check_output", side_effect=check_output):
                API["install_control"]()
            rebased = json.loads(suite.journal.read_text())
            for key in ("before", "applied"):
                self.assertEqual(rebased[key]["bar"]["layout"]["center"][0]["id"], "cogitator.control")
            self.assertEqual(rebased["before"]["bar"]["layout"]["center"][1]["id"], "omarchy.clock")
            self.assertEqual(json.loads(suite.config.read_text())["bar"]["layout"]["center"][0]["id"], "cogitator.control")


if __name__ == "__main__":
    unittest.main()
