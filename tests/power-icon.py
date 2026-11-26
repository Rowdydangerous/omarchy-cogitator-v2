#!/usr/bin/env python3
"""Render the packaged power button through the native optical icon normalizer."""
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ICONS = runpy.run_path(str(ROOT / "scripts/icon-style.py"))
VOICE = runpy.run_path(str(ROOT / "scripts/voice-style.py"))


class PowerIconTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("quickshell"), "requires Quickshell")
    def test_percentage_does_not_shrink_battery_art(self):
        with tempfile.TemporaryDirectory() as work:
            work = Path(work)
            shutil.copytree(ROOT / "plugins/power", work, dirs_exist_ok=True)
            ICONS["apply_icons"](work)
            raw = (work / "Panel.qml").read_text()
            start = raw.index("  BarIconButton {")
            button = raw[start:VOICE["expression_end"](raw, raw.index("{", start))]
            for name in ("Commons", "Ui"):
                (work / name).symlink_to(Path("/usr/share/omarchy/shell") / name, target_is_directory=True)
            cases = [{"font": font, "percent": percent, "shown": shown, "vertical": vertical}
                     for font in (12, 18, 24) for percent in (9, 80, 100)
                     for shown in (False, True) for vertical in (False, True)]
            qml = '''import QtQuick
import QtQuick.Window
import qs.Commons
import qs.Ui
import "icons" as CogitatorIcons
Window {
  id: root
  visible: true; width: 260; height: 80
  property bool showPercentage: true
  property real batteryFraction: 0.8
  property bool discharging: false
  property bool charging: false
  property bool batteryPresent: true
  property QtObject bar: QtObject {
    property string fontFamily: "monospace"
    property color barForeground: "#4fd06a"
    property color background: "#030704"
    property color urgent: "#ff5345"
    property bool vertical: false
    property int barSize: 40
    function hideTooltip(item) {}
    function showTooltip(item, text) {}
  }
  function batteryIcon() { return ""; }
  function togglePercentage() { showPercentage = !showPercentage; }
  function toggle() {}
  Item {
    width: button.implicitWidth; height: button.implicitHeight
''' + button + '''
  }
  property var cases: ''' + json.dumps(cases) + '''
  property int index: 0
  property var records: []
  Timer {
    id: setup; interval: 10; running: true
    onTriggered: {
      var test = root.cases[root.index];
      Style.fontBaseSize = test.font;
      root.showPercentage = test.shown;
      root.batteryFraction = test.percent / 100;
      root.bar.vertical = test.vertical;
      inspect.start();
    }
  }
  Timer {
    id: inspect; interval: 80
    onTriggered: {
      root.records.push({test: root.cases[root.index],
        height: button.componentPaintedHeight, target: Style.bar.iconSize,
        sourceWidth: button.componentSourceBounds.width,
        label: button.labelText, nativeLabel: button.nativeReserveLabel});
      root.index++;
      if (root.index < root.cases.length) setup.start();
      else { console.log("POWER_ICON " + JSON.stringify(root.records)); Qt.quit(); }
    }
  }
}
'''
            file = work / "shell.qml"
            file.write_text(qml)
            result = subprocess.run(["quickshell", "-p", str(file), "--no-color"],
                                    env=dict(os.environ, QT_QPA_PLATFORM="offscreen"),
                                    capture_output=True, text=True, timeout=20)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            for error in ("ReferenceError", "TypeError", "Binding loop"):
                self.assertNotIn(error, output)
            captures = [line.split("POWER_ICON ", 1)[1] for line in output.splitlines()
                        if "POWER_ICON " in line]
            self.assertTrue(captures, output)
            records = json.loads(captures[-1])
            self.assertEqual(len(records), len(cases))
            widths = {}
            for record in records:
                test = record["test"]
                self.assertTrue(record["nativeLabel"], record)
                self.assertAlmostEqual(record["height"], record["target"], delta=0.5, msg=record)
                label = str(test["percent"]) + "%" if test["shown"] and not test["vertical"] else ""
                self.assertEqual(record["label"], label, record)
                key = test["font"]
                if key not in widths:
                    widths[key] = record["sourceWidth"]
                self.assertAlmostEqual(record["sourceWidth"], widths[key], delta=0.5, msg=record)


if __name__ == "__main__":
    unittest.main()
