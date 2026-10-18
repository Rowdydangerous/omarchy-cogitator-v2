#!/usr/bin/env python3
"""Detached regression probe for enable-time crashes after the icon rollback."""
import json
from pathlib import Path
import runpy
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
api = runpy.run_path(str(ROOT / "scripts/control-backend.py"))
report_path = api["STATE"] / "backups" / f"enable-stability-{time.time_ns()}.json"
report = {"result": "running", "checks": []}


def crashes():
    result = subprocess.run(["coredumpctl", "--no-pager", "--no-legend", "list", "quickshell"], capture_output=True, text=True)
    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr)
    return set(result.stdout.splitlines())


def note(text):
    report["checks"].append(text)
    api["atomic_write"](report_path, api["json_bytes"](report))
    print(text, flush=True)


def transition(action, engaged):
    api["queue"](action)
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        state = api["status"]()
        if not state["busy"] and state["operation"].get("phase") == "failed":
            raise RuntimeError(state["operation"].get("message", "Transition failed"))
        if not state["busy"] and state["engaged"] == engaged and state["operation"].get("phase") == "completed":
            note(action + " completed")
            return
        time.sleep(1)
    raise RuntimeError(action + " timed out")


try:
    state = api["status"]()
    assert not state["busy"], "Another transition is already running"
    before = crashes()
    report["baselineCoredumps"] = sorted(before)
    if state["engaged"]:
        transition("disable", False)
    transition("enable", True)
    time.sleep(15)
    new = crashes() - before
    report["newCoredumps"] = sorted(new)
    assert not new, "A new Quickshell crash was recorded"
    assert subprocess.check_output(["omarchy-shell", "shell", "ping"], text=True).strip() == "ok"
    note("Shell responds after 15-second observation; no new coredumps")
    report["result"] = "pass"
except Exception as error:
    report.update(result="fail", error=str(error))
finally:
    api["atomic_write"](report_path, api["json_bytes"](report))
    print(json.dumps(report), flush=True)
    print(f"Proof saved: {report_path}", flush=True)
if report["result"] != "pass":
    raise SystemExit(1)
