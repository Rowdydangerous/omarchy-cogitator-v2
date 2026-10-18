#!/usr/bin/env python3
"""Detached live controller cycle proof; restores the initially off desktop."""
import json
from pathlib import Path
import runpy
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
api = runpy.run_path(str(ROOT / "scripts/control-backend.py"))
report_path = api["STATE"] / "backups" / f"control-proof-{time.time_ns()}.json"
report = {"result": "running", "checks": []}


def record(check):
    report["checks"].append(check)
    api["atomic_write"](report_path, api["json_bytes"](report))
    print(check, flush=True)


def wait(engaged):
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        state = api["status"]()
        if not state["busy"] and state["operation"].get("phase") == "failed":
            raise RuntimeError(state["operation"].get("message", "Transition failed"))
        if not state["busy"] and state["engaged"] == engaged and state["operation"].get("phase") == "completed":
            return state
        time.sleep(1)
    raise RuntimeError("Controller transition timed out")


def control_present():
    catalog = json.loads(subprocess.check_output(["omarchy-shell", "shell", "listPlugins"], text=True))
    assert any(p["id"] == "cogitator.control" and p["enabled"] for p in catalog)
    config = json.loads((Path.home() / ".config/omarchy/shell.json").read_text())
    found = False
    clocks = {"omarchy.clock", "cogitator.clock"}
    clocks.update(p["id"] for p in catalog if p.get("clonedFrom") == "omarchy.clock")
    for entries in config["bar"]["layout"].values():
        for index, entry in enumerate(entries[:-1]):
            if api["SUITE"]["entry_id"](entry) == "cogitator.control" and api["SUITE"]["entry_id"](entries[index + 1]) in clocks:
                found = True
    assert found, "Controller no longer precedes the clock"


try:
    original = api["status"]()
    assert not original["engaged"] and not original["busy"], "Start this proof while disengaged"
    control_present()
    record("Controller enabled beside stock clock while disengaged")
    api["queue"]("enable")
    wait(True)
    control_present()
    record("Controller enabled beside replacement clock after engagement")
    api["queue"]("disable")
    wait(False)
    control_present()
    record("Controller remained enabled beside restored stock clock")
    report["result"] = "pass"
except Exception as error:
    report.update(result="fail", error=str(error))
finally:
    api["atomic_write"](report_path, api["json_bytes"](report))
    print(json.dumps(report), flush=True)
    print(f"Proof saved: {report_path}", flush=True)
if report["result"] != "pass":
    raise SystemExit(1)
