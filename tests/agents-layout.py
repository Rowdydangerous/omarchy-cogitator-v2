#!/usr/bin/env python3
"""Agent chart labels remain compact and cannot paint over their bars."""
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
LAYOUT = runpy.run_path(str(ROOT / "scripts/layout-style.py"))["agents_layout"]


class AgentLayoutTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("quickshell"), "requires Quickshell")
    def test_today_and_long_day_labels_fit_the_reserved_column(self):
        original = (ROOT / "plugins/agents/Panel.qml").read_text()
        with tempfile.TemporaryDirectory() as work:
            work = Path(work)
            (work / "manifest.json").write_text('{"id":"cogitator.agents"}')
            (work / "Panel.qml").write_text(original)
            LAYOUT(work / "Panel.qml")
            VOICE["apply_voice"](work)
            raw = (work / "Panel.qml").read_text()
            self.assertNotIn("CogitatorVoice.say(root.dayLabel(", raw)
            self.assertEqual(json.loads((ROOT / "shared/voice/lexicon.json").read_text())["Today"], "Current Cycle")
            start = raw.index("component DayRow:")
            component = raw[start:VOICE["expression_end"](raw, raw.index("{", start))]
            for name in ("Commons", "Ui"):
                (work / name).symlink_to(Path("/usr/share/omarchy/shell") / name, target_is_directory=True)
            qml = '''import QtQuick
import QtQuick.Window
import qs.Commons
import qs.Ui
import "voice/Lexicon.js" as CogitatorVoice
Window {
  id: root
  width: 400; height: 160; visible: true
  property color foreground: "#4fd06a"
  property color dim: "#2f5b38"
  property color track: "#1d3a24"
  property string fontFamily: "Monaspace Xenon Frozen"
  property QtObject usage: QtObject { function formatTokenCount(value) { return "3.5M"; } }
  function clamp(value, low, high) { return Math.max(low, Math.min(high, value)); }
  function alpha(color, opacity) { return Qt.rgba(color.r, color.g, color.b, opacity); }
  function dayLabel(date, today) { return today ? "Today" : "VeryLongLocalizedWeekday"; }
  function dayTooltip(day, today) { return "fixture tooltip"; }
''' + component + '''
  Column {
    width: parent.width
    DayRow { id: todayRow; width: parent.width; today: true; ratio: 0.5 }
    DayRow { id: otherRow; width: parent.width; today: false; ratio: 0.5 }
  }
  function geometry(row) {
    var label = row.children[0];
    var bar = row.children[1];
    return {text: label.text, width: label.width, painted: label.contentWidth,
            right: label.x + label.width, barLeft: bar.x};
  }
  Timer { interval: 50; running: true; onTriggered: { Style.fontBaseSize = 18; check.start(); } }
  Timer {
    id: check; interval: 150
    onTriggered: { console.log("AGENT_LAYOUT " + JSON.stringify([root.geometry(todayRow), root.geometry(otherRow)])); Qt.quit(); }
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
            self.assertNotIn("ReferenceError", output)
            records = [line.split("AGENT_LAYOUT ", 1)[1] for line in output.splitlines() if "AGENT_LAYOUT " in line]
            self.assertTrue(records, output)
            records = json.loads(records[-1])
            self.assertEqual(records[0]["text"], "Today")
            for record in records:
                self.assertLessEqual(record["painted"], record["width"] + 1)
                self.assertGreater(record["barLeft"], record["right"])
        self.assertEqual((ROOT / "plugins/agents/Panel.qml").read_text(), original)


if __name__ == "__main__":
    unittest.main()
