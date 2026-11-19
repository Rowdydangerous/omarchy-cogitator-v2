#!/usr/bin/env python3
"""Exercise shared popup geometry with strip-sized and full-screen native bars."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PopupGeometryTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("quickshell"), "requires Quickshell")
    def test_native_and_legacy_bars_leave_usable_controller_space(self):
        raw = (ROOT / "shared/frames/KeyboardPanel.qml").read_text()
        geometry = raw[raw.index("  readonly property real screenW:"):
                       raw.index("  // --- popout coordination")]
        with tempfile.TemporaryDirectory() as work:
            work = Path(work)
            (work / "Commons").symlink_to("/usr/share/omarchy/shell/Commons", target_is_directory=True)
            cases = [{"position": position, "native": native, "small": small, "pageHeight": height}
                     for position in ("top", "bottom", "left", "right")
                     for native in (False, True) for small in (False, True)
                     for height in (420, 650)]
            qml = '''import QtQuick
import QtQuick.Window
import qs.Commons
Window {
  visible: true; width: 100; height: 100
  Item {
    id: root
    property var screen: ({width: 1600, height: 1000, name: "fixture"})
    property var bar: ({position: "top", barSize: 26})
    property var anchorWindow: ({width: 1600, height: 26})
    property Item anchorItem: Item {}
    property point anchorScreenPos: Qt.point(800, 13)
    property real anchorW: 26
    property real anchorH: 26
    property string barPos: bar.position
    property bool centerOnBar: false
    property int margin: 12
    property int gap: 12
    property int padding: 18
    property var borderSpec: Border.none()
    property real pageHeight: 420
    property real contentWidth: fittedContentWidth(560)
    property real contentHeight: cappedContentHeight(pageHeight)
''' + geometry + '''
    property var cases: ''' + json.dumps(cases) + '''
    property int index: 0
    property var results: []
    Timer {
      id: setup; interval: 10; running: true
      onTriggered: {
        var test = root.cases[root.index];
        root.screen = {width: test.small ? 1000 : 1600, height: test.small ? 500 : 1000, name: "fixture"};
        root.bar = test.native
          ? {position: test.position, barSize: 26, barSizeFor: function(name) { return name === "fixture" ? 34 : 26; }}
          : {position: test.position, barSize: 26};
        var horizontal = test.position === "top" || test.position === "bottom";
        root.anchorWindow = test.native
          ? {width: root.screen.width, height: root.screen.height}
          : {width: horizontal ? root.screen.width : 26, height: horizontal ? 26 : root.screen.height};
        root.anchorScreenPos = horizontal ? Qt.point(root.screen.width / 2, 13) : Qt.point(13, root.screen.height / 2);
        root.pageHeight = test.pageHeight;
        inspect.start();
      }
    }
    Timer {
      id: inspect; interval: 10
      onTriggered: {
        root.results.push({test: root.cases[root.index], thickness: root.barThickness,
          width: root.contentWidth, height: root.contentHeight,
          x: root.cardOrigin.x, y: root.cardOrigin.y,
          screenWidth: root.screenW, screenHeight: root.screenH});
        root.index++;
        if (root.index < root.cases.length) setup.start();
        else { console.log("POPUP_GEOMETRY " + JSON.stringify(root.results)); Qt.quit(); }
      }
    }
  }
}
'''
            file = work / "shell.qml"
            file.write_text(qml)
            result = subprocess.run(["quickshell", "-p", str(file), "--no-color"],
                                    env=dict(os.environ, QT_QPA_PLATFORM="offscreen"),
                                    capture_output=True, text=True, timeout=15)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            for error in ("ReferenceError", "TypeError", "Binding loop"):
                self.assertNotIn(error, output)
            records = [line.split("POPUP_GEOMETRY ", 1)[1] for line in output.splitlines()
                       if "POPUP_GEOMETRY " in line]
            self.assertTrue(records, output)
            records = json.loads(records[-1])
            self.assertEqual(len(records), len(cases))
            for record in records:
                test = record["test"]
                thickness = 34 if test["native"] else 26
                horizontal = test["position"] in ("top", "bottom")
                expected_height = min(test["pageHeight"], record["screenHeight"] -
                                      (thickness + 24 if horizontal else 24))
                self.assertEqual(record["thickness"], thickness, record)
                self.assertEqual(record["height"], expected_height, record)
                self.assertEqual(record["width"], 560, record)
                self.assertGreaterEqual(record["height"], 420, record)
                self.assertGreaterEqual(record["x"], 12, record)
                self.assertGreaterEqual(record["y"], 12, record)
                self.assertLessEqual(record["x"] + record["width"], record["screenWidth"] - 12, record)
                self.assertLessEqual(record["y"] + record["height"], record["screenHeight"] - 12, record)
                if test["position"] == "top":
                    self.assertEqual(record["y"], thickness + 12, record)
                elif test["position"] == "bottom":
                    self.assertEqual(record["y"] + record["height"], record["screenHeight"] - thickness - 12, record)


if __name__ == "__main__":
    unittest.main()
