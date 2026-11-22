#!/usr/bin/env python3
"""Exercise the installed controller against the host's real plugin bar facade."""
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
API = runpy.run_path(str(ROOT / "scripts/control-backend.py"))
WAYLAND = runpy.run_path(str(ROOT / "tests/wayland-fixture.py"))["headless_wayland"]


class ControllerLayoutTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("quickshell") and shutil.which("sway"), "requires Quickshell and Sway")
    def test_controller_controls_remain_reachable_with_native_facade(self):
        with tempfile.TemporaryDirectory() as work:
            work = Path(work)
            shutil.copytree(ROOT / "control", work / "control")
            shutil.copytree(ROOT / "shared/frames", work / "control/frames")
            for name in ("Commons", "Ui"):
                (work / name).symlink_to(Path("/usr/share/omarchy/shell") / name, target_is_directory=True)
            status = {"values": API["settings"](""), "revision": "fixture", "schema": API["SCHEMA"],
                      "engaged": False, "busy": False, "suite": "inactive"}
            (work / "control/status.json").write_text(json.dumps(status))
            (work / "control/backend.py").write_text(
                'import json, pathlib, sys\n'
                'root = pathlib.Path(__file__).parent\n'
                'if sys.argv[1] == "status": print((root / "status.json").read_text())\n'
                'else:\n'
                '    with (root / "actions.jsonl").open("a") as file: file.write(json.dumps(sys.argv[1:]) + "\\n")\n'
                '    print(json.dumps({"ok": True, "message": "Fixture completed"}))\n')
            cases = [{"position": position, "legacy": legacy, "engaged": engaged, "page": page}
                     for position, legacy in (("top", False), ("bottom", False),
                                              ("left", False), ("right", False), ("top", True))
                     for engaged in (False, True)
                     for page in ("Overview", "Appearance", "Surfaces", "Motion")]
            qml = r'''import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui as Ui
import "control" as Control
ShellRoot {
  PanelWindow {
    id: host
    property bool legacy: false
    anchors {
      top: !host.legacy || facade.position !== "bottom"
      bottom: !host.legacy || facade.position === "bottom"
      left: true; right: true
    }
    implicitHeight: host.legacy ? 26 : 0
    visible: true
    exclusiveZone: host.legacy ? 0 : 64
    exclusionMode: host.legacy ? ExclusionMode.Auto : ExclusionMode.Normal
    FileView { id: fixture; path: Qt.resolvedUrl("control/status.json").toString().replace(/^file:\/\//, ""); blockLoading: true }
    Ui.PluginBarApi {
      id: facade
      pluginId: "cogitator.control"; moduleName: "cogitator.control"
      barSize: 26; position: "top"; fontFamily: "monospace"
      vertical: position === "left" || position === "right"
      foreground: "white"; barForeground: "white"; background: "black"; urgent: "red"
    }
    Control.Panel {
      id: controller
      bar: facade
      x: facade.position === "right" ? host.width - width : facade.vertical ? 0 : host.width / 2
      y: facade.position === "bottom" ? host.height - height : facade.vertical ? host.height / 2 : 0
      width: implicitWidth; height: implicitHeight
    }
    function popup() {
      for (var i = 0; i < controller.data.length; i++) {
        var object = controller.data[i];
        if (typeof object.cappedContentHeight === "function") return object;
      }
      throw new Error("Controller popup not found");
    }
    function items() {
      var result = [], queue = [];
      var content = host.popup().contentItem;
      for (var i = 0; i < content.length; i++) queue.push(content[i]);
      while (queue.length) {
        var item = queue.shift();
        if (result.indexOf(item) !== -1) continue;
        result.push(item);
        if (item.children) for (var j = 0; j < item.children.length; j++) queue.push(item.children[j]);
      }
      return result;
    }
    function button(label) {
      var all = host.items();
      for (var i = 0; i < all.length; i++)
        if (all[i].text === label && typeof all[i].clicked === "function") return all[i];
      throw new Error("Button not found: " + label);
    }
    function rect(item) {
      var point = item.mapToItem(null, 0, 0);
      return {x: point.x, y: point.y, width: item.width, height: item.height,
              visible: item.visible, enabled: item.enabled};
    }
    function scrollView() {
      var all = host.items();
      for (var i = 0; i < all.length; i++)
        if (typeof all[i].availableWidth === "number" && all[i].contentItem &&
            typeof all[i].contentItem.contentY === "number") return all[i];
      throw new Error("Controller scroll view not found");
    }
    property var cases: ''' + json.dumps(cases) + '''
    property int index: 0
    property var results: []
    property var current: ({})
    Timer {
      id: setup; interval: 30; running: true
      onTriggered: {
        if (controller.fields.length !== 22 || controller.busy) { setup.start(); return; }
        var test = host.cases[host.index];
        host.legacy = test.legacy;
        facade.position = test.position;
        var data = JSON.parse(fixture.text());
        data.engaged = test.engaged;
        data.revision = "case-" + host.index + "-" + host.screen.height;
        fixture.setText(JSON.stringify(data));
        controller.dirty = false;
        controller.refresh();
        ready.start();
      }
    }
    Timer {
      id: ready; interval: 30
      onTriggered: {
        if (controller.revision !== "case-" + host.index + "-" + host.screen.height) {
          controller.refresh(); ready.start(); return;
        }
        var test = host.cases[host.index];
        host.button(test.page).clicked();
        controller.open();
        inspect.start();
      }
    }
    Timer {
      id: inspect; interval: 60
      onTriggered: {
        var panel = host.popup();
        var test = host.cases[host.index];
        var scroll = host.scrollView();
        host.current = {test: test, x: panel.cardOrigin.x, y: panel.cardOrigin.y,
          gap: panel.gap, thickness: panel.barThickness, width: panel.contentWidth,
          height: panel.contentHeight, screenWidth: panel.screenW, screenHeight: panel.screenH,
          hasPerScreenMethod: typeof facade.barSizeFor === "function",
          zone: panel.anchorWindow.exclusiveZone, scroll: host.rect(scroll),
          apply: host.rect(host.button("Apply")), tabs: []};
        var names = ["Overview", "Appearance", "Surfaces", "Motion"];
        for (var i = 0; i < names.length; i++) host.current.tabs.push(host.rect(host.button(names[i])));
        if (test.page === "Overview") {
          var engage = host.button(test.engaged ? "Disengage Cogitator" : "Engage Cogitator");
          scroll.contentItem.contentY = 0;
          host.current.engage = host.rect(engage);
          engage.clicked();
        }
        edit.start();
      }
    }
    Timer {
      id: edit; interval: 30
      onTriggered: {
        if (controller.busy) { edit.start(); return; }
        controller.setValue("TEXT_STREAMING", !controller.saved.TEXT_STREAMING);
        save.start();
      }
    }
    Timer {
      id: save; interval: 30
      onTriggered: {
        host.current.applyEnabledAfterEdit = host.button("Apply").enabled;
        host.current.warningInk = String(controller.warningInk);
        host.button("Apply").clicked();
        complete.start();
      }
    }
    Timer {
      id: complete; interval: 30
      onTriggered: {
        if (controller.busy) { complete.start(); return; }
        host.results.push(host.current);
        host.index++;
        if (host.index < host.cases.length) setup.start();
        else { console.log("CONTROL_LAYOUT " + JSON.stringify(host.results)); Qt.quit(); }
      }
    }
  }
}
'''
            file = work / "shell.qml"
            file.write_text(qml)
            for height in (500, 1000):
                with self.subTest(height=height), WAYLAND(height=height) as env:
                    try:
                        result = subprocess.run(["quickshell", "-p", str(file), "--no-color"],
                                                env=env, capture_output=True, text=True, timeout=30)
                    except subprocess.TimeoutExpired as error:
                        self.fail((error.stdout or b"").decode() + (error.stderr or b"").decode())
                    output = result.stdout + result.stderr
                    self.assertEqual(result.returncode, 0, output)
                    for error in ("ReferenceError", "TypeError", "Binding loop", "Unable to assign"):
                        self.assertNotIn(error, output)
                    captures = [line.split("CONTROL_LAYOUT ", 1)[1] for line in output.splitlines()
                                if "CONTROL_LAYOUT " in line]
                    self.assertTrue(captures, output)
                    records = json.loads(captures[-1])
                    self.assertEqual(len(records), len(cases))
                    for record in records:
                        test = record["test"]
                        self.assertFalse(record["hasPerScreenMethod"], record)
                        self.assertEqual(record["thickness"], 26 if test["legacy"] else 64, record)
                        # Independently check that the card clears the real strip.
                        if test["position"] == "top":
                            self.assertGreaterEqual(record["y"], record["thickness"], record)
                        elif test["position"] == "bottom":
                            self.assertLessEqual(record["y"] + record["height"], height - 64, record)
                        elif test["position"] == "left":
                            self.assertGreaterEqual(record["x"], 64, record)
                        else:
                            self.assertLessEqual(record["x"] + record["width"], record["screenWidth"] - 64, record)
                        self.assertGreater(record["scroll"]["height"], 80, record)
                        self.assertLessEqual(record["scroll"]["y"] + record["scroll"]["height"],
                                             record["apply"]["y"], record)
                        self.assertFalse(record["apply"]["enabled"], record)
                        for button in record["tabs"] + [record["apply"]]:
                            self.assertTrue(button["visible"], record)
                            self.assertGreater(button["width"], 0, record)
                            self.assertGreaterEqual(button["y"], record["y"], record)
                            self.assertLessEqual(button["y"] + button["height"],
                                                 record["y"] + record["height"], record)
                        self.assertTrue(record["applyEnabledAfterEdit"], record)
                        self.assertEqual(record["warningInk"], "#e0ad2f")
                        if "engage" in record:
                            engage = record["engage"]
                            self.assertTrue(engage["visible"] and engage["enabled"], record)
                            self.assertGreaterEqual(engage["y"], record["scroll"]["y"], record)
                            self.assertLessEqual(engage["y"] + engage["height"],
                                                 record["scroll"]["y"] + record["scroll"]["height"], record)
            actions = [json.loads(line) for line in (work / "control/actions.jsonl").read_text().splitlines()]
            self.assertEqual(sum(action[0] == "save" for action in actions), len(cases) * 2)
            self.assertEqual(sum(action[0] == "engage" for action in actions), 10)
            self.assertEqual(sum(action[0] == "disengage" for action in actions), 10)


if __name__ == "__main__":
    unittest.main()
