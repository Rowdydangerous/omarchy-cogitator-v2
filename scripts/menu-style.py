#!/usr/bin/env python3
"""Stage menu compatibility without altering the imported stock baseline."""
import json
from pathlib import Path


def apply_menu(stage):
    stage = Path(stage)
    manifest = stage / "manifest.json"
    if not manifest.exists() or json.loads(manifest.read_text()).get("id") != "cogitator.menu":
        return
    file = stage / "Menu.qml"
    raw = file.read_text()
    original = '  readonly property var appLibrary: root.shell ? root.shell.appLibrary : null'
    replacement = '''  // Some shell versions omit appLibrary on the scoped third-party menu
  // API. Instantiate the host's native library only in that case, rather than
  // silently showing zero apps or bypassing its hidden-entry rules.
  readonly property var appLibrary: root.shell && root.shell.appLibrary
    ? root.shell.appLibrary : nativeAppLibrary.item

  Loader {
    id: nativeAppLibrary
    active: !!root.shell && !root.shell.appLibrary
    sourceComponent: HostServices.AppLibrary { omarchyPath: root.omarchyPath }
  }'''
    if original not in raw:
        raise RuntimeError("Stock menu appLibrary binding changed; compatibility adapter needs review")
    file.write_text('import qs.services as HostServices\n' + raw.replace(original, replacement, 1))
