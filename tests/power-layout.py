#!/usr/bin/env python3
"""Power labels and full values stay inside the available stats columns."""
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
VOICE = runpy.run_path(str(ROOT / "scripts/voice-style.py"))
LAYOUT = runpy.run_path(str(ROOT / "scripts/layout-style.py"))


class PowerLayoutTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("quickshell"), "requires Quickshell")
    def test_long_labels_and_watts_fit(self):
        with tempfile.TemporaryDirectory() as work:
            work = Path(work)
            panel = work / "Panel.qml"
            shutil.copy2(ROOT / "plugins/power/Panel.qml", panel)
            LAYOUT["power_layout"](panel)
            raw = panel.read_text()
            components = []
            for name in ("InfoPair", "InfoLabel", "InfoValue"):
                start = raw.index("component " + name + ":")
                components.append(raw[start:VOICE["expression_end"](raw, raw.index("{", start))])
            (work / "Commons").symlink_to("/usr/share/omarchy/shell/Commons", target_is_directory=True)
            for width, font in ((180, 12), (180, 18), (280, 12), (280, 18)):
                qml = '''import QtQuick
import QtQuick.Window
import qs.Commons
Window {
 id: root
 visible: true; width: ''' + str(width) + '''; height: 400
 property var bar: ({foreground: "#4fd06a", fontFamily: "monospace"})
 Column {
   id: rows; width: parent.width; spacing: 8
   InfoPair { label: "Drawing from Power Cells"; value: "123.45W" }
   InfoPair { label: "Replenishment Cycles"; value: "123456" }
   InfoPair { label: "Reserve Endurance"; value: "12h 59m" }
 }
''' + "\n".join(components) + '''
 Timer { interval: 30; running: true; onTriggered: { Style.fontBaseSize = ''' + str(font) + '''; inspect.start(); } }
 Timer {
   id: inspect; interval: 100
   onTriggered: {
     var result = [];
     for (var i = 0; i < rows.children.length; i++) {
       var row = rows.children[i], texts = [];
       for (var j = 0; j < row.children.length; j++) {
         var item = row.children[j];
         if (typeof item.text === "string")
           texts.push({x: item.x, width: item.width, painted: item.contentWidth, text: item.text});
       }
       result.push({height: row.height, texts: texts});
     }
     console.log("POWER_LAYOUT " + JSON.stringify(result)); Qt.quit();
   }
 }
}
'''
                file = work / "shell.qml"
                file.write_text(qml)
                result = subprocess.run(["quickshell", "-p", str(file), "--no-color"],
                                        env=dict(os.environ, QT_QPA_PLATFORM="offscreen"),
                                        capture_output=True, text=True, timeout=10)
                output = result.stdout + result.stderr
                self.assertEqual(result.returncode, 0, output)
                captures = [line.split("POWER_LAYOUT ", 1)[1] for line in output.splitlines() if "POWER_LAYOUT " in line]
                self.assertTrue(captures, output)
                for row in json.loads(captures[-1]):
                    label, value = row["texts"]
                    self.assertGreater(row["height"], 0)
                    self.assertLessEqual(label["x"] + label["width"], value["x"], row)
                    for item in row["texts"]:
                        self.assertLessEqual(item["x"] + item["width"], width + 0.5, (width, font, row))
                        self.assertLessEqual(item["painted"], item["width"] + 0.5, row)


if __name__ == "__main__":
    unittest.main()
