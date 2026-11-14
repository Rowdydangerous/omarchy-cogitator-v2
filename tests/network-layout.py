#!/usr/bin/env python3
"""Render staged network details at narrow widths and enlarged font sizes."""
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAYOUT = runpy.run_path(str(ROOT / "scripts/layout-style.py"))["network_layout"]
VOICE = runpy.run_path(str(ROOT / "scripts/voice-style.py"))


class NetworkLayoutTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("quickshell"), "requires Quickshell")
    def test_long_addresses_never_overlap_labels_and_copy_text_stays_complete(self):
        original = (ROOT / "plugins/network/Panel.qml").read_text()
        with tempfile.TemporaryDirectory() as work:
            work = Path(work)
            (work / "manifest.json").write_text('{"id":"cogitator.network"}')
            (work / "Panel.qml").write_text(original)
            LAYOUT(work / "Panel.qml")
            VOICE["apply_voice"](work)
            raw = (work / "Panel.qml").read_text()
            self.assertIn("panel.fittedContentWidth(Style.space(540))", raw)
            self.assertIn("onClicked: root.copyToClipboard(parent.text)", raw)
            for name in ("Commons", "Ui"):
                (work / name).symlink_to(Path("/usr/share/omarchy/shell") / name, target_is_directory=True)

            def extract(start):
                return raw[start:VOICE["expression_end"](raw, raw.index("{", start))]

            details = extract(raw.index("      Column {", raw.index("// Connection details:")))
            components = "\n".join(extract(raw.index("component " + name + ":")) for name in ("InfoLabel", "InfoValue", "DetailValue"))
            for width, font_size in ((540, 12), (280, 12), (540, 18), (280, 18)):
                qml = '''import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import qs.Commons
import qs.Ui
import "voice/Lexicon.js" as CogitatorVoice
Window {
  id: root
  visible: true; width: ''' + str(width) + '''; height: 800
  property QtObject bar: QtObject { property color foreground: "#4fd06a"; property color urgent: "#ff5345"; property string fontFamily: "Monaspace Xenon Frozen" }
  property var info: ({iface: "fixture", ip: "ffff:ffff:ffff:ffff:ffff:ffff:255.255.255.255/128", gateway: "fe80:ffff:ffff:ffff:ffff:ffff:ffff:ffff%enp123s456", rx_bytes: "123456789", tx_bytes: "123456789"})
  property bool hasTransferStats: true
  property real downloadRate: 999
  property real uploadRate: 999
  property real internetPingLatency: 99
  property real internetPingPacketLoss: 0
  property bool longValues: true
  property var before: ({})
  function formatPingLatency(value) { return longValues ? "999.99 ms" : "0 ms"; }
  function formatPacketLoss(value) { return longValues ? "100.00%" : "0%"; }
  function formatRate(value) { return longValues ? "999.99 MiB/s" : "0 B/s"; }
  function formatBytes(value) { return longValues ? "999.99 GiB" : "0 B"; }
  function copyToClipboard(value) { }
  Item {
    id: container
    width: parent.width
''' + details + '''
  }
''' + components + '''
  function inspectLayout() {
    var rows = [];
    var addresses = [];
    var grids = container.children[0].children;
    for (var g = 0; g < grids.length; g++) {
      var children = grids[g].children;
      for (var i = 0; i < children.length; i++) {
        var item = children[i];
        if (typeof item.text !== "string") continue;
        rows.push({x: item.x, y: item.y, width: item.width, height: item.height, group: g, text: item.text});
        if (item.text === root.info.ip || item.text === root.info.gateway)
          addresses.push({text: item.text, width: item.width, content: item.contentWidth});
      }
    }
    return {rows: rows, addresses: addresses};
  }
  Timer { interval: 50; running: true; onTriggered: { Style.fontBaseSize = ''' + str(font_size) + '''; check.start(); } }
  Timer {
    id: check; interval: 150
    onTriggered: { root.before = root.inspectLayout(); root.longValues = false; shortCheck.start(); }
  }
  Timer {
    id: shortCheck; interval: 150
    onTriggered: { console.log("NETWORK_LAYOUT " + JSON.stringify({long: root.before, short: root.inspectLayout()})); Qt.quit(); }
  }
}
'''
                (work / "shell.qml").write_text(qml)
                result = subprocess.run(["quickshell", "-p", str(work / "shell.qml"), "--no-color"],
                                        env=dict(os.environ, QT_QPA_PLATFORM="offscreen"),
                                        capture_output=True, text=True, timeout=15)
                output = result.stdout + result.stderr
                self.assertEqual(result.returncode, 0, output)
                self.assertNotIn("Binding loop", output)
                self.assertNotIn("ReferenceError", output)
                records = [line.split("NETWORK_LAYOUT ", 1)[1] for line in output.splitlines() if "NETWORK_LAYOUT " in line]
                self.assertTrue(records, output)
                captures = json.loads(records[-1])
                record = captures["long"]
                self.assertEqual(len(record["rows"]), len(captures["short"]["rows"]))
                for before, after in zip(record["rows"], captures["short"]["rows"]):
                    self.assertAlmostEqual(before["x"], after["x"], places=2,
                                           msg=(width, font_size, before, after))
                    self.assertAlmostEqual(before["width"], after["width"], places=2,
                                           msg=(width, font_size, before, after))
                self.assertEqual(len(record["addresses"]), 2)
                for address in record["addresses"]:
                    self.assertLessEqual(address["content"], address["width"] + 1)
                for i, item in enumerate(record["rows"]):
                    self.assertGreaterEqual(item["x"], -1)
                    self.assertLessEqual(item["x"] + item["width"], width + 1)
                    for other in record["rows"][i + 1:]:
                        if item["group"] != other["group"]:
                            continue
                        overlaps = (item["x"] + item["width"] > other["x"] + 0.5
                                    and other["x"] + other["width"] > item["x"] + 0.5
                                    and item["y"] + item["height"] > other["y"] + 0.5
                                    and other["y"] + other["height"] > item["y"] + 0.5)
                        self.assertFalse(overlaps, (width, font_size, item, other))
        self.assertEqual((ROOT / "plugins/network/Panel.qml").read_text(), original)


if __name__ == "__main__":
    unittest.main()
