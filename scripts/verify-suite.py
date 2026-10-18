#!/usr/bin/env python3
"""Check live routing or wait for detached restoration and save its proof."""
import argparse
import base64
import importlib.util
import json
from pathlib import Path
import subprocess
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("action", choices=["active", "restored"])
parser.add_argument("backup", type=Path)
parser.add_argument("--wait", type=int, default=0)
args = parser.parse_args()
state = args.backup.parent.parent
deadline = time.monotonic() + args.wait
while args.action == "restored" and ((state / "suite.json").exists() or (state / "snapshot.json").exists()):
    if time.monotonic() >= deadline:
        raise SystemExit("Restore has not completed; recovery journals retained")
    time.sleep(1)
journal_path = state / "suite.json" if args.action == "active" else args.backup / "suite-journal.json"
journal = json.loads(journal_path.read_text())
catalog = json.loads(subprocess.check_output(["omarchy-shell", "shell", "listPlugins"], text=True))
plugins = {p["id"]: p for p in catalog}
config = Path.home() / ".config/omarchy/shell.json"
if args.action == "active":
    assert journal["phase"] == "active"
    live = json.loads(config.read_text())
    assert live["bar"]["id"] == journal["applied"]["bar"]["id"]
    assert live["bar"].get("centerAnchor") == journal["applied"]["bar"].get("centerAnchor")
    for selected in journal["selected"]:
        assert plugins[selected["replacementId"]]["enabled"], selected
    for original in journal["mapping"]:
        assert not plugins[original]["enabled"], original
    report = {"result": "pass", "phase": "active", "replacements": len(journal["selected"]),
              "configEditedWhileEngaged": live != journal["applied"]}
else:
    assert journal["phase"] == "restored"
    spec = importlib.util.spec_from_file_location("suite", Path(__file__).with_name("cogitator-suite.py"))
    suite = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(suite)
    expected = suite.rollback_config(journal["before"], journal["applied"], journal["restoreInput"])
    assert expected == journal["restoredConfig"]
    original = journal["originalBytes"]
    if expected != journal["before"]:
        assert json.loads(config.read_text()) == expected, "Engaged edits were not preserved"
    elif original is None:
        assert not config.exists(), "Original absent config was not restored"
    else:
        assert config.read_bytes() == base64.b64decode(original), "Config is not byte-identical to baseline"
    for original_plugin in journal["catalog"]:
        assert plugins[original_plugin["id"]]["enabled"] == original_plugin["enabled"], original_plugin["id"]
    for plugin in catalog:
        if plugin["id"].startswith("cogitator.") and plugin["id"] != "cogitator.control":
            assert not plugin["enabled"], plugin["id"]
    report = {"result": "pass", "phase": "restored", "config":
              "engaged-edits-preserved" if expected != journal["before"] else "byte-identical",
              "priorPluginStates": "matched", "suitePlugins": "inactive"}
report_path = args.backup / f"live-proof-{args.action}.json"
report_path.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report))
print(f"Proof saved: {report_path}")
