#!/usr/bin/env python3
"""Persistent controller installer, validated settings API and detached worker."""
import argparse
import base64
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import runpy
import shlex
import shutil
import subprocess
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = Path(json.loads((HERE / "runtime.json").read_text())["project"]) if (HERE / "runtime.json").exists() else HERE.parent
SUITE = runpy.run_path(str(ROOT / "scripts/cogitator-suite.py"))
atomic_write, json_bytes = SUITE["atomic_write"], SUITE["json_bytes"]
CONTROL = "cogitator.control"
MARKER = ".cogitator-control.json"
CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
STATE = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "cogitator-v2"
CONF = CONFIG_HOME / "cogitator-v2/cogitator.conf"
OPERATION = STATE / "control-operation.json"
SCHEMA = json.loads((ROOT / "control/settings-schema.json").read_text())


def parse_conf(raw):
    values = {}
    for line in raw.splitlines():
        if "=" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        try:
            tokens = shlex.split(value, comments=True)
        except ValueError:
            continue
        values[key.strip()] = " ".join(tokens)
    return values


def revision(raw):
    return hashlib.sha256(raw.encode()).hexdigest()


def validate(values):
    known = {field["key"] for field in SCHEMA}
    unknown = set(values) - known
    if unknown:
        raise ValueError("Unknown settings: " + ", ".join(sorted(unknown)))
    result = {}
    for field in SCHEMA:
        key, kind = field["key"], field["type"]
        value = values.get(key, field["default"])
        if kind == "boolean":
            if isinstance(value, str):
                if value.lower() not in ("true", "false", "yes", "no", "1", "0"):
                    raise ValueError(f"{key}: expected true/false")
                value = value.lower() in ("true", "yes", "1")
            if not isinstance(value, bool):
                raise ValueError(f"{key}: expected true/false")
        elif kind == "number":
            if isinstance(value, bool):
                raise ValueError(f"{key}: expected a number")
            value = float(value)
            if not math.isfinite(value) or not field["min"] <= value <= field["max"]:
                raise ValueError(f"{key}: expected {field['min']}–{field['max']}")
            if field["step"] == 1:
                if value != round(value):
                    raise ValueError(f"{key}: expected a whole number")
                value = int(value)
        elif kind == "choice":
            if value not in field["choices"]:
                raise ValueError(f"{key}: invalid selection")
        elif kind == "color":
            import re
            if value and not re.fullmatch(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?", str(value)):
                raise ValueError("Custom phosphor must be #RGB or #RRGGBB")
        result[key] = value
    if result["PALETTE"] == "custom" and not result["CUSTOM_PHOSPHOR"]:
        raise ValueError("Choose a custom phosphor color before selecting the custom palette")
    return result


def settings(raw):
    parsed = parse_conf(raw)
    effective = {}
    # Reading old hand-edited files follows the renderer's effective bounds;
    # opening the panel must not fail or rewrite the file because of old values.
    for field in SCHEMA:
        key = field["key"]
        value = parsed.get(key, field["default"])
        if field["type"] == "number":
            try:
                value = float(value)
                if not math.isfinite(value):
                    value = field["default"]
                value = max(field["min"], min(field["max"], value))
                if field["step"] == 1:
                    value = int(value)
            except (TypeError, ValueError):
                value = field["default"]
        elif field["type"] == "boolean":
            value = str(value).lower() in ("true", "yes", "1")
        elif field["type"] == "choice" and value not in field["choices"]:
            value = field["default"]
        elif field["type"] == "color":
            import re
            if value and not re.fullmatch(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?", str(value)):
                value = ""
        effective[key] = value
    return effective


def write_settings(raw, values):
    pending = dict(values)
    lines = []
    for line in raw.splitlines():
        key = line.split("=", 1)[0].strip() if "=" in line else ""
        if key in values and not line.lstrip().startswith("#"):
            if key in pending:
                value = pending.pop(key)
                lines.append(key + "=" + (str(value).lower() if isinstance(value, bool) else json.dumps(value)))
            continue
        lines.append(line)
    for key, value in pending.items():
        lines.append(key + "=" + (str(value).lower() if isinstance(value, bool) else json.dumps(value)))
    return "\n".join(lines) + "\n"


def place_control(config, catalog):
    result = copy.deepcopy(config)
    layout = result.setdefault("bar", {}).setdefault("layout", {})
    for section in ("left", "center", "right"):
        layout.setdefault(section, [])
    if any(SUITE["entry_id"](e) == CONTROL for entries in layout.values() for e in entries):
        return result
    clocks = {"omarchy.clock", "cogitator.clock"}
    clocks.update(p["id"] for p in catalog if p.get("clonedFrom") == "omarchy.clock")
    anchor = result["bar"].get("centerAnchor")
    for allowed in ({anchor} if anchor in clocks else set(), clocks):
        for section, entries in layout.items():
            for index, entry in enumerate(entries):
                if SUITE["entry_id"](entry) in allowed:
                    entries.insert(index, {"id": CONTROL})
                    return result
    layout["center"].insert(0, {"id": CONTROL})
    return result


def hashes(directory):
    return {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in directory.rglob("*") if p.is_file() and p.name != MARKER}


def install_control():
    suite = SUITE["Suite"]()
    if suite.config.is_symlink():
        raise RuntimeError("shell.json is a symlink; preserved")
    target = suite.plugins / CONTROL
    if target.is_symlink():
        raise RuntimeError("Controller destination is a symlink; preserved")
    if target.exists() and (not (target / MARKER).exists() or json.loads((target / MARKER).read_text())["files"] != hashes(target)):
        raise RuntimeError("Controller contains foreign or local edits; preserved")
    backup = STATE / "backups" / f"control-{time.time_ns()}"
    backup.mkdir(parents=True)
    raw = suite.config.read_bytes() if suite.config.exists() else None
    if raw is not None:
        atomic_write(backup / "shell-before.json", raw)
    receipt = STATE / "control-install.json"
    if not receipt.exists():
        atomic_write(receipt, json_bytes({"originalAbsent": raw is None, "backup": str(backup)}))
    suite.plugins.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".control-", dir=suite.plugins))
    changed_install = False
    try:
        shutil.copytree(ROOT / "control", stage, dirs_exist_ok=True)
        shutil.copy2(ROOT / "scripts/control-backend.py", stage / "backend.py")
        shutil.copytree(ROOT / "shared/frames", stage / "frames")
        atomic_write(stage / "runtime.json", json_bytes({"project": str(ROOT)}))
        subprocess.run(["omarchy", "plugin", "validate", str(stage)], check=True, stdout=subprocess.DEVNULL)
        candidate_hashes = hashes(stage)
        if not target.exists() or candidate_hashes != hashes(target):
            atomic_write(stage / MARKER, json_bytes({"files": candidate_hashes}))
            if target.exists():
                target.rename(backup / "previous-plugin")
            stage.rename(target)
            changed_install = True
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    catalog = json.loads(subprocess.check_output(["omarchy-shell", "shell", "listPlugins"], text=True))
    before = json.loads(raw) if raw is not None else json.loads(suite.defaults.read_text())
    config = place_control(before, catalog)
    config["disabledPlugins"] = [p for p in config.get("disabledPlugins", []) if p != CONTROL]
    if not config["disabledPlugins"]:
        config.pop("disabledPlugins", None)
    if config != before:
        atomic_write(suite.config, json_bytes(config), suite.config.stat().st_mode & 0o777 if raw is not None else 0o644)
    # Installation during an existing engagement is an explicit persistent edit.
    # Rebase BOTH sides, retaining the old journal in recovery storage.
    if suite.journal.exists():
        journal = json.loads(suite.journal.read_text())
        rebased = {key: place_control(journal[key], catalog) for key in ("before", "applied")}
        if any(rebased[key] != journal[key] for key in rebased):
            atomic_write(backup / "suite-before.json", json_bytes(journal))
            journal.update(rebased)
            journal["originalBytes"] = base64.b64encode(json_bytes(journal["before"])).decode()
            journal["catalog"] = [p for p in journal["catalog"] if p["id"] != CONTROL]
            journal["catalog"].append({"id": CONTROL, "enabled": True, "kinds": ["bar-widget"], "clonedFrom": ""})
            suite.save(journal)
    if not OPERATION.exists():
        atomic_write(OPERATION, json_bytes({"phase": "idle", "message": "Control sanctum ready"}))
    if changed_install:
        subprocess.run(["omarchy-shell", "shell", "rescanPlugins"], check=True, stdout=subprocess.DEVNULL)
    print("Control widget installed beside the clock; available while disengaged.")


def uninstall_control():
    suite = SUITE["Suite"]()
    target = suite.plugins / CONTROL
    if not target.exists():
        return
    if target.is_symlink() or not (target / MARKER).exists() or json.loads((target / MARKER).read_text())["files"] != hashes(target):
        raise RuntimeError("Edited controller preserved; remove it manually when ready")
    receipt = STATE / "control-install.json"
    origin = json.loads(receipt.read_text()) if receipt.exists() else {}
    # Native removal preserves a plugin backup and removes all layout references.
    subprocess.run(["omarchy", "plugin", "remove", CONTROL, "--yes"], check=True)
    if origin.get("originalAbsent") and suite.config.exists():
        restored = json.loads(suite.config.read_text())
        defaults = json.loads(suite.defaults.read_text())
        if restored == defaults:
            suite.config.unlink()
    receipt.unlink(missing_ok=True)


def status():
    raw = CONF.read_text() if CONF.exists() else (ROOT / "config/cogitator.conf.example").read_text()
    operation = json.loads(OPERATION.read_text()) if OPERATION.exists() else {"phase": "idle"}
    unit = subprocess.run(["systemctl", "--user", "is-active", "cogitator-v2-transition.service"], capture_output=True, text=True)
    busy = unit.stdout.strip() in ("active", "activating", "deactivating")
    if operation.get("phase") in ("queued", "running") and not busy and time.time() - operation.get("started", 0) > 15:
        operation = {"phase": "failed", "message": "Transition interrupted; retry or inspect transition logs"}
    journal = STATE / "suite.json"
    phase = json.loads(journal.read_text())["phase"] if journal.exists() else "inactive"
    return {"values": settings(raw), "revision": revision(raw), "schema": SCHEMA,
            "engaged": (STATE / "snapshot.json").exists() or phase in ("active", "switching"),
            "busy": busy or operation.get("phase") in ("queued", "running"), "operation": operation,
            "suite": phase}


def queue(action, payload=None):
    current = status()
    if current["busy"]:
        raise RuntimeError("A transition is already in progress")
    if payload is not None:
        raw = CONF.read_text()
        if payload.get("revision") != revision(raw):
            raise RuntimeError("Settings changed outside this panel. Revert to reload before applying.")
        values = validate(payload["values"])
        before = settings(raw)
        changed = payload.get("changed", list(values))
        if not isinstance(changed, list) or any(key not in values for key in changed):
            raise ValueError("Invalid changed-settings list")
        backup = STATE / "backups" / f"settings-{time.time_ns()}.conf"
        atomic_write(backup, raw.encode())
        atomic_write(CONF, write_settings(raw, {key: values[key] for key in changed}).encode(), CONF.stat().st_mode & 0o777)
        if not current["engaged"]:
            atomic_write(OPERATION, json_bytes({"phase": "completed", "action": "save", "message": "Settings saved for the next engagement"}))
            return {"ok": True, "message": "Settings saved for the next engagement"}
        payload = {"paletteChanged": ("PALETTE" in changed and before["PALETTE"] != values["PALETTE"]) or
                   (values["PALETTE"] == "custom" and "CUSTOM_PHOSPHOR" in changed and before["CUSTOM_PHOSPHOR"] != values["CUSTOM_PHOSPHOR"]),
                   "changed": changed}
    else:
        payload = {}
    operation = {"phase": "queued", "action": action, "started": time.time(), "message": "Rite queued"}
    atomic_write(OPERATION, json_bytes(operation))
    result = subprocess.run(["systemd-run", "--user", "--collect", "--unit=cogitator-v2-transition",
                             "python3", str(ROOT / "scripts/control-backend.py"), "worker", action, json.dumps(payload)],
                            capture_output=True, text=True)
    if result.returncode:
        operation.update(phase="failed", message=result.stderr.strip())
        atomic_write(OPERATION, json_bytes(operation))
        raise RuntimeError(operation["message"])
    return {"ok": True, "message": "Transition queued"}


def worker(action, payload):
    operation = {"phase": "running", "action": action, "started": time.time(), "message": "Performing " + action + " rite"}
    atomic_write(OPERATION, json_bytes(operation))
    env = dict(os.environ, COGITATOR_FOREGROUND="1")
    try:
        if action == "apply" and payload.get("paletteChanged"):
            subprocess.run([str(ROOT / "scripts/cogitator"), "palette", settings(CONF.read_text())["PALETTE"]], env=env, check=True)
        command = [str(ROOT / "scripts/cogitator"), action]
        if action == "apply":
            command = [str(ROOT / "scripts/cogitator"), "settings-apply"] + payload.get("changed", [])
        subprocess.run(command, env=env, check=True)
        operation.update(phase="completed", message="Rite completed")
    except Exception as error:
        operation.update(phase="failed", message=str(error) + "; inspect transition logs for details")
        raise
    finally:
        atomic_write(OPERATION, json_bytes(operation))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["install", "uninstall", "status", "save", "engage", "disengage", "worker", "config-value", "logs"])
    parser.add_argument("arguments", nargs="*")
    args = parser.parse_args()
    if args.action == "install":
        install_control()
    elif args.action == "uninstall":
        uninstall_control()
    elif args.action == "status":
        print(json.dumps(status()))
    elif args.action == "logs":
        logs = subprocess.check_output(["journalctl", "--user", "-u", "cogitator-v2-transition.service", "-n", "12", "--no-pager", "-o", "cat"], text=True)
        print(json.dumps({"ok": True, "message": logs.strip()}))
    elif args.action == "config-value":
        key, fallback = args.arguments
        print(parse_conf(CONF.read_text()).get(key, fallback))
    elif args.action == "worker":
        worker(args.arguments[0], json.loads(args.arguments[1]))
    else:
        result = queue("apply", json.loads(args.arguments[0])) if args.action == "save" else queue("enable" if args.action == "engage" else "disable")
        print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(json.dumps({"ok": False, "message": str(error)}))
        raise SystemExit(1)
