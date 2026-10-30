#!/usr/bin/env python3
"""Exercise the menu fallback with native Qt/Quickshell and fixture apps."""
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ADAPT = runpy.run_path(str(ROOT / "scripts/menu-style.py"))["apply_menu"]
HOST = Path("/usr/share/omarchy/shell")


class MenuTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("quickshell"), "requires Quickshell")
    def test_app_result_activation_launches_selected_id_without_launcher_handoff(self):
        source = (ROOT / "overlays/rowdy.menu/Menu.qml").read_text()
        activation = "  function activateIndex" + source.split("  function activateIndex", 1)[1].split("  function requestDeleteSelected", 1)[0]
        with tempfile.TemporaryDirectory() as work:
            work = Path(work)
            # A regression must not accidentally send openLauncher IPC to the
            # real desktop from this isolated activation test.
            binary = work / "bin/omarchy-shell"
            binary.parent.mkdir()
            binary.write_text("#!/bin/sh\nexit 0\n")
            binary.chmod(0o755)
            qml = '''import QtQuick
import Quickshell
ShellRoot {
  id: root
  property bool deleteConfirmOpen: false
  property bool dmenuActive: false
  property string mode: "select"
  property string filterText: "actual"
  property bool opened: true
  property int applySerial: 0
  property int requestSerial: 17
  property var launches: []
  property var selections: []
  property var routes: []
  property var actions: []
  property QtObject appLibrary: QtObject {
    function launch(id, label) { root.launches = root.launches.concat([{id: id, label: label}]); }
  }
  function applyDmenuSelection(value) { selections = selections.concat([value]); }
  function setActiveMenu(id) { routes = routes.concat([id]); }
  function applySelected(id, action) { actions = actions.concat([{id: id, action: action}]); }
  ListModel { id: displayModel }
''' + activation + '''
  Timer {
    interval: 50; running: true
    onTriggered: {
      displayModel.append({kind: "app", appId: "actual-budget", label: "Actual Budget", itemId: "apps.actual-budget", detail: ""});
      root.activateIndex(0, false);
      var closed = !root.opened && root.filterText === "" && root.applySerial === 17;
      root.activateIndex(0, true);
      root.activateIndex(-1, false);
      root.activateIndex(99, false);
      displayModel.clear();
      displayModel.append({kind: "menu", target: "apps", itemId: "apps"});
      root.activateIndex(0, false);
      displayModel.clear();
      displayModel.append({kind: "action", itemId: "trigger.capture.screenshot", action: "native-screenshot"});
      root.activateIndex(0, false);
      displayModel.clear();
      displayModel.append({kind: "dmenu", label: "Keep raw", detail: "stable-id"});
      root.dmenuActive = true;
      root.activateIndex(0, false);
      console.log("ACTIVATION_TEST " + JSON.stringify({launches: root.launches,
        closed: closed, routes: root.routes, actions: root.actions, selections: root.selections}));
      Qt.quit();
    }
  }
}
'''
            (work / "shell.qml").write_text(qml)
            env = dict(os.environ, QT_QPA_PLATFORM="offscreen", PATH=str(binary.parent) + ":" + os.environ["PATH"])
            result = subprocess.run(["quickshell", "-p", str(work / "shell.qml"), "--no-color"],
                                    env=env, capture_output=True, text=True, timeout=15)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            line = next(line.split("ACTIVATION_TEST ", 1)[1] for line in output.splitlines() if "ACTIVATION_TEST " in line)
            record = json.loads(line)
            self.assertEqual(record["launches"], [{"id": "actual-budget", "label": "Actual Budget"}] * 2)
            self.assertTrue(record["closed"])
            self.assertEqual(record["routes"], ["apps"])
            self.assertEqual(record["actions"], [{"id": "trigger.capture.screenshot", "action": "native-screenshot"}])
            self.assertEqual(record["selections"], ["Keep raw\tstable-id"])

    def test_stock_baseline_is_untouched_and_adapter_checks_its_anchor(self):
        original = (ROOT / "plugins/menu/Menu.qml").read_text()
        with tempfile.TemporaryDirectory() as work:
            stage = Path(work)
            (stage / "manifest.json").write_text('{"id":"cogitator.menu"}')
            (stage / "Menu.qml").write_text(original)
            ADAPT(stage)
            self.assertIn("HostServices.AppLibrary", (stage / "Menu.qml").read_text())
            (stage / "Menu.qml").write_text("changed upstream")
            with self.assertRaises(RuntimeError):
                ADAPT(stage)
        self.assertEqual((ROOT / "plugins/menu/Menu.qml").read_text(), original)

    @unittest.skipUnless(shutil.which("quickshell") and HOST.is_dir(), "requires Omarchy/Quickshell")
    def test_native_fallback_lists_fixture_apps_and_respects_hidden_entries(self):
        with tempfile.TemporaryDirectory() as work:
            work = Path(work)
            (work / "manifest.json").write_text('{"id":"cogitator.menu"}')
            (work / "Menu.qml").write_text((ROOT / "plugins/menu/Menu.qml").read_text())
            ADAPT(work)
            adapted = (work / "Menu.qml").read_text()
            block = adapted.split("  // Some shell versions", 1)[1].split("  property bool deleteConfirmOpen", 1)[0]
            block = "  // Some shell versions" + block
            for directory in ("services", "Commons"):
                (work / directory).symlink_to(HOST / directory, target_is_directory=True)
            apps = work / "data/applications"
            apps.mkdir(parents=True)
            for identity, name in (("aether", "Aether"), ("actual-budget", "Actual Budget"),
                                   ("Basecamp", "Basecamp"), ("btop", "Hidden by Omarchy"),
                                   ("hidden", "NoDisplay Helper")):
                extra = "NoDisplay=true\n" if identity == "hidden" else ""
                (apps / f"{identity}.desktop").write_text(
                    f"[Desktop Entry]\nType=Application\nName={name}\nExec=true\n{extra}")
            qml = '''import QtQuick
import Quickshell
import qs.services as HostServices
ShellRoot {
  id: root
  property var shell: ({appLibrary: null})
  property string omarchyPath: "/usr/share/omarchy"
''' + block + '''
  QtObject { id: suppliedLibrary }
  Timer {
    interval: 1500; running: true
    onTriggered: {
      var names = root.appLibrary.sortedEntries("").map(function(row) { return row.entry.name; });
      var usedFallback = nativeAppLibrary.active;
      root.shell = ({appLibrary: suppliedLibrary});
      console.log("MENU_LIBRARY_TEST " + JSON.stringify({names: names,
        fallback: usedFallback, supplied: root.appLibrary === suppliedLibrary,
        fallbackStopped: !nativeAppLibrary.active}));
      Qt.quit();
    }
  }
}
'''
            (work / "shell.qml").write_text(qml)
            env = dict(os.environ, HOME=str(work), XDG_DATA_HOME=str(work / "data"),
                       XDG_DATA_DIRS=str(work / "empty-data"), QT_QPA_PLATFORM="offscreen")
            result = subprocess.run(["quickshell", "-p", str(work / "shell.qml"), "--no-color"],
                                    env=env, capture_output=True, text=True, timeout=15)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            line = next(line.split("MENU_LIBRARY_TEST ", 1)[1] for line in output.splitlines()
                        if "MENU_LIBRARY_TEST " in line)
            record = json.loads(line)
            self.assertEqual(record["names"], ["Actual Budget", "Aether", "Basecamp"])
            self.assertTrue(record["fallback"])
            self.assertTrue(record["supplied"])
            self.assertTrue(record["fallbackStopped"])


if __name__ == "__main__":
    unittest.main()
