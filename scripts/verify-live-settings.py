#!/usr/bin/env python3
"""Check a reversible controller setting change keeps Quickshell's PID."""
import json
from pathlib import Path
import runpy
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
api = runpy.run_path(str(ROOT / "scripts/control-backend.py"))


def shell_pid():
    layers = json.loads(subprocess.check_output(["hyprctl", "layers", "-j"], text=True))
    for output in layers.values():
        for entries in output["levels"].values():
            for entry in entries:
                if entry.get("namespace") == "omarchy-bar":
                    return entry["pid"]
    raise RuntimeError("No shell bar found")


def apply(values, rev):
    api["queue"]("apply", {"values": values, "revision": rev, "changed": ["WORKSPACE_RITES"]})
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        status = api["status"]()
        if not status["busy"] and status["operation"].get("phase") == "completed":
            return status
        if status["operation"].get("phase") == "failed":
            raise RuntimeError(status["operation"]["message"])
        time.sleep(0.2)
    raise RuntimeError("Settings transition timed out")


original = api["CONF"].read_text()
status = api["status"]()
assert status["engaged"] and not status["busy"]
before_pid = shell_pid()
values = dict(status["values"])
values["WORKSPACE_RITES"] = not values["WORKSPACE_RITES"]
updated = apply(values, status["revision"])
assert shell_pid() == before_pid, "Settings restarted Quickshell"
assert json.loads((api["CONFIG_HOME"] / "cogitator-v2/config.json").read_text())["workspaceRites"] == values["WORKSPACE_RITES"]
restored = apply(status["values"], updated["revision"])
assert shell_pid() == before_pid, "Restoring the setting restarted Quickshell"
# Preserve original quoting/comments too, provided there were no concurrent edits.
assert api["revision"](api["CONF"].read_text()) == restored["revision"]
api["atomic_write"](api["CONF"], original.encode(), api["CONF"].stat().st_mode & 0o777)
report = {"result": "pass", "shellPid": before_pid, "restarts": 0,
          "change": "WORKSPACE_RITES toggled and restored", "config": "original bytes restored"}
path = api["STATE"] / "backups" / f"live-settings-proof-{time.time_ns()}.json"
api["atomic_write"](path, api["json_bytes"](report))
print(json.dumps(report))
print(f"Proof saved: {path}")
