#!/usr/bin/env python3
"""Transactional installation and routing for stock-based Cogitator plugins.

Never edits existing custom clones. A journal precedes all live writes; config
switching is atomic and rollback preserves unrelated edits made while engaged.
"""
import argparse
import base64
import copy
import hashlib
import json
import os
import runpy
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ".cogitator-suite.json"


def entry_id(entry):
    return entry.get("id", "") if isinstance(entry, dict) else entry


def remap_entry(entry, mapping):
    result = copy.deepcopy(entry)
    if isinstance(result, dict):
        result["id"] = mapping.get(entry_id(result), entry_id(result))
    else:
        result = mapping.get(result, result)
    return result


def plan_config(config, catalog, baselines, with_rite=False):
    """Map every instance; do not enable absent widgets or disabled services."""
    result = copy.deepcopy(config)
    layout = config.get("bar", {}).get("layout", {})
    references = {entry_id(e) for section in layout.values() for e in section}
    references.update(entry_id(e) for e in config.get("plugins", []))
    references.add(config.get("bar", {}).get("id", "omarchy.bar"))
    mapping = {}
    selected = []
    for baseline in baselines:
        source, replacement = baseline["sourceId"], baseline["replacementId"]
        candidates = [p for p in catalog if p["id"] == source or p.get("clonedFrom") == source]
        active = [p for p in candidates if p.get("enabled") and
                  (p.get("kinds") != ["bar-widget"] or p["id"] in references)]
        if not active:
            continue
        mapping[source] = replacement
        for plugin in active:
            mapping[plugin["id"]] = replacement
        selected.append({"sourceId": source, "replacementId": replacement,
                         "kinds": active[0]["kinds"]})
    bar = result.setdefault("bar", {})
    for section, entries in bar.get("layout", {}).items():
        bar["layout"][section] = [remap_entry(e, mapping) for e in entries]
    if "omarchy.bar" in mapping or bar.get("id") in mapping:
        bar["id"] = mapping.get(bar.get("id", "omarchy.bar"), bar.get("id"))
    if bar.get("centerAnchor") in mapping:
        bar["centerAnchor"] = mapping[bar["centerAnchor"]]
    result["plugins"] = [remap_entry(e, mapping) for e in result.get("plugins", [])]
    present = {entry_id(e) for e in result["plugins"]}
    present.update(entry_id(e) for entries in bar.get("layout", {}).values() for e in entries)
    for plugin in selected:
        if any(k not in ("bar", "bar-widget") for k in plugin["kinds"]) and plugin["replacementId"] not in present:
            result["plugins"].append({"id": plugin["replacementId"]})
            present.add(plugin["replacementId"])
    disabled = result.setdefault("disabledPlugins", [])
    for original in mapping:
        if original not in disabled:
            disabled.append(original)
    # Existing disabled suite IDs from an earlier cycle must not mask selection.
    result["disabledPlugins"] = [p for p in disabled if p not in mapping.values()]
    if with_rite:
        result["disabledPlugins"] = [p for p in result["disabledPlugins"] if p != "cogitator-rite"]
        if "cogitator-rite" not in present:
            result["plugins"].append({"id": "cogitator-rite"})
    return result, mapping, selected


def rollback_config(before, applied, current):
    """Three-way undo: retain edits outside managed routing, including settings.

    For ambiguous edits to repeated instances with different original clone IDs,
    refuse to guess. The journal and recovery copies remain available.
    """
    if current == applied:
        return copy.deepcopy(before)
    missing = object()
    widget_pairs = []
    for section, originals in before.get("bar", {}).get("layout", {}).items():
        widget_pairs.extend(zip(originals, applied.get("bar", {}).get("layout", {}).get(section, [])))

    def undo(old, expected, live, path=()):
        if live == expected:
            return copy.deepcopy(old) if old is not missing else missing
        if old == expected:
            return copy.deepcopy(live) if live is not missing else missing
        if all(isinstance(v, dict) for v in (old, expected, live)):
            out = {}
            for key in old.keys() | expected.keys() | live.keys():
                value = undo(old.get(key, missing), expected.get(key, missing), live.get(key, missing), path + (key,))
                if value is not missing:
                    out[key] = value
            return out
        if isinstance(expected, list) and isinstance(live, list):
            old_list = old if isinstance(old, list) else []
            if path == ("disabledPlugins",):
                added = set(expected) - set(old_list)
                removed = set(old_list) - set(expected)
                restored = [v for v in live if v not in added] + [v for v in old_list if v in removed and v not in live]
                return missing if old is missing and not restored else restored
            if path == ("plugins",) or path[:2] == ("bar", "layout"):
                # Expected and original entries correspond by index; appended
                # infrastructure entries have no original and are dropped.
                pairs = list(zip(old_list, expected))
                used = set()
                out = []
                appended = expected[len(old_list):]
                for entry in live:
                    candidates = [(i, a, b) for i, (a, b) in enumerate(pairs)
                                  if i not in used and entry_id(b) == entry_id(entry)]
                    exact = [c for c in candidates if c[2] == entry]
                    if exact:
                        candidates = exact
                    if candidates:
                        originals = {entry_id(c[1]) for c in candidates}
                        if len(originals) != 1:
                            raise RuntimeError(f"Ambiguous changed clone instances in {'.'.join(path)}; restore journal kept")
                        i, a, b = candidates[0]
                        used.add(i)
                        out.append(remap_entry(entry, {entry_id(b): entry_id(a)}))
                    elif any(entry_id(entry) == entry_id(a) for a in appended):
                        continue
                    else:
                        if path[:2] == ("bar", "layout"):
                            # Widgets may have moved between bar sections.
                            moved = [(a, b) for a, b in widget_pairs if entry_id(b) == entry_id(entry)]
                            exact_moved = [(a, b) for a, b in moved if b == entry]
                            if exact_moved:
                                moved = exact_moved
                            originals = {entry_id(a) for a, b in moved}
                            if len(originals) > 1:
                                raise RuntimeError("Ambiguous moved clone instance; restore journal kept")
                            if moved:
                                out.append(remap_entry(entry, {entry_id(entry): entry_id(moved[0][0])}))
                                continue
                        # A newly added/repeated suite widget returns to its
                        # stock identity when it has no captured original.
                        identity = entry_id(entry)
                        out.append(remap_entry(entry, {identity: identity.replace("cogitator.", "omarchy.", 1)})
                                   if isinstance(identity, str) and identity.startswith("cogitator.")
                                   else copy.deepcopy(entry))
                return out
        # Scalar routing we changed must not retain a reference to the suite.
        if path in (("bar", "id"), ("bar", "centerAnchor")):
            if isinstance(live, str) and live.startswith("cogitator."):
                originals = {entry_id(a) for a, b in widget_pairs if entry_id(b) == live}
                if len(originals) == 1:
                    return originals.pop()
                if len(originals) > 1:
                    raise RuntimeError("Ambiguous changed bar anchor; restore journal kept")
                return live.replace("cogitator.", "omarchy.", 1)
            return copy.deepcopy(live) if live is not missing else missing
        raise RuntimeError(f"Conflicting change in {'.'.join(path)}; restore journal kept")

    return undo(before, applied, current)


def atomic_write(path, data, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".cogitator-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def json_bytes(value):
    return (json.dumps(value, indent=2) + "\n").encode()


def file_hashes(directory):
    return {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in directory.rglob("*") if p.is_file() and p.name != RECEIPT}


class Suite:
    def __init__(self, root=ROOT, config_home=None, state_home=None, defaults=None, run=None):
        self.root = Path(root)
        config_home = Path(config_home or os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        state_home = Path(state_home or os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
        self.config = config_home / "omarchy/shell.json"
        self.plugins = config_home / "omarchy/plugins"
        self.state = state_home / "cogitator-v2"
        self.journal = self.state / "suite.json"
        self.defaults = Path(defaults or Path(os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")) / "config/omarchy/shell.json")
        self.run = run or (lambda args: subprocess.check_output(args, text=True))
        self.baselines = json.loads((self.root / "docs/stock-baseline.json").read_text())["plugins"]

    def save(self, journal):
        atomic_write(self.journal, json_bytes(journal))

    def prepare(self, with_rite=False):
        if self.config.is_symlink():
            raise RuntimeError("shell.json is a symlink; preserved (suite requires a regular user config)")
        if self.journal.exists():
            journal = json.loads(self.journal.read_text())
            if journal["phase"] == "restored":
                raise RuntimeError("Previous restore awaits completion")
            return journal
        raw = self.config.read_bytes() if self.config.exists() else None
        before = json.loads(raw) if raw is not None else json.loads(self.defaults.read_bytes())
        catalog = json.loads(self.run(["omarchy-shell", "shell", "listPlugins"]))
        applied, mapping, selected = plan_config(before, catalog, self.baselines, with_rite)
        backup = self.state / "backups" / f"suite-{time.time_ns()}"
        backup.mkdir(parents=True)
        if raw is not None:
            atomic_write(backup / "shell-before.json", raw, self.config.stat().st_mode & 0o777)
        atomic_write(backup / "catalog-before.json", json_bytes(catalog))
        journal = {"version": 1, "phase": "prepared", "backup": str(backup),
                   "originalBytes": base64.b64encode(raw).decode() if raw is not None else None,
                   "originalMode": self.config.stat().st_mode & 0o777 if raw is not None else 0o644,
                   "before": before, "applied": applied, "mapping": mapping,
                   "selected": selected, "catalog": catalog, "installed": []}
        self.save(journal)
        return journal

    def install(self, journal):
        self.plugins.mkdir(parents=True, exist_ok=True)
        # Preflight all collisions before installing anything.
        for plugin in self.baselines:
            target = self.plugins / plugin["replacementId"]
            if target.is_symlink():
                raise RuntimeError(f"Refusing symlink plugin destination: {target}")
            if target.exists():
                receipt = target / RECEIPT
                if not receipt.is_file() or json.loads(receipt.read_text()).get("files") != file_hashes(target):
                    raise RuntimeError(f"Existing plugin is foreign or locally edited: {target}; preserved")
        batch = Path(tempfile.mkdtemp(prefix=".cogitator-stage-", dir=self.plugins))
        pending = []
        try:
            for plugin in self.baselines:
                target = self.plugins / plugin["replacementId"]
                stage = batch / plugin["replacementId"]
                stage.mkdir()
                shutil.copytree(self.root / plugin["path"], stage, dirs_exist_ok=True)
                if plugin["sourceId"] == "omarchy.menu":
                    shutil.copy2(self.root / "overlays/rowdy.menu/Menu.qml", stage / "Menu.qml")
                if plugin["sourceId"] == "omarchy.notifications":
                    self.run(["python3", str(self.root / "scripts/apply-notification-overlay.py"),
                              str(stage / "Service.qml"), str(self.root / "overlays/notifications/NotificationCard.qml")])
                # Local copies preserve popup focus/position/dismissal logic;
                # only the outer surfaces and shared frame imports change.
                runpy.run_path(str(ROOT / "scripts/frame-style.py"))["apply_frames"](stage, self.root)
                if plugin["sourceId"] == "omarchy.weather":
                    runpy.run_path(str(ROOT / "scripts/layout-style.py"))["weather_layout"](stage / "Panel.qml")
                runpy.run_path(str(ROOT / "scripts/voice-style.py"))["apply_voice"](stage, self.root)
                runpy.run_path(str(ROOT / "scripts/icon-style.py"))["apply_icons"](stage, self.root)
                self.run(["omarchy", "plugin", "validate", str(stage)])
                candidate_hashes = file_hashes(stage)
                if target.exists() and candidate_hashes == file_hashes(target):
                    continue
                atomic_write(stage / RECEIPT, json_bytes({"sourceId": plugin["sourceId"], "files": candidate_hashes}))
                pending.append((plugin, stage, target))
            # Finish all slow copying/validation before publishing any roots.
            # The watcher can coalesce this short rename batch into one reload.
            for plugin, stage, target in pending:
                if plugin["replacementId"] not in journal["installed"]:
                    journal["installed"].append(plugin["replacementId"])
            if pending:
                self.save(journal)
            for plugin, stage, target in pending:
                if target.exists():
                    old = Path(journal["backup"]) / f"install-{plugin['replacementId']}-{time.time_ns()}"
                    target.rename(old)
                stage.rename(target)
        finally:
            shutil.rmtree(batch, ignore_errors=True)

    def enable(self):
        if not self.journal.exists():
            raise RuntimeError("Prepare the suite before enabling it")
        journal = json.loads(self.journal.read_text())
        self.sync_runtime(journal)
        if journal["phase"] == "active":
            print("Suite already active; original snapshot preserved.")
            return
        self.install(journal)
        self.run(["omarchy-shell", "shell", "rescanPlugins"])
        expected = {p["replacementId"] for p in self.baselines}
        for _ in range(100):
            discovered = {p["id"] for p in json.loads(self.run(["omarchy-shell", "shell", "listPlugins"]))}
            if expected <= discovered:
                break
            time.sleep(0.05)
        else:
            raise RuntimeError("Installed suite was not fully discovered; config was not switched")
        # Record the pre-switch config too: native installer may have added the
        # coordinator since prepare. Never discard those bytes without a copy.
        if self.config.exists():
            atomic_write(Path(journal["backup"]) / "shell-before-switch.json", self.config.read_bytes())
        journal["phase"] = "switching"
        self.save(journal)
        atomic_write(self.config, json_bytes(journal["applied"]), journal["originalMode"])
        journal["phase"] = "active"
        self.save(journal)
        print(f"Suite active: {len(journal['selected'])} replacements; original clones preserved.")

    def refresh(self):
        if not self.journal.exists():
            return
        journal = json.loads(self.journal.read_text())
        if journal["phase"] != "active":
            raise RuntimeError("Suite must be active before refreshing plugin sources")
        self.sync_runtime(journal)
        self.install(journal)
        self.run(["omarchy-shell", "shell", "rescanPlugins"])
        print("Suite sources refreshed; routing and original snapshot preserved.")

    def sync_runtime(self, journal):
        """Deploy the working-tree console code without discarding user edits."""
        core = self.plugins / "cogitator-rite"
        target = core / "qml"
        source = self.root / "qml"
        if not core.exists() or not source.exists():
            return
        if core.is_symlink() or not (core / ".cogitator-v2-installed").is_file():
            raise RuntimeError("Coordinator installation is foreign; preserved")
        receipt = core / ".cogitator-runtime.json"
        if receipt.exists():
            if json.loads(receipt.read_text())["files"] != file_hashes(target):
                raise RuntimeError("Coordinator QML has local edits; preserved")
        else:
            # A native checkout is safe only while the tracked QML is pristine.
            status = self.run(["git", "-C", str(core), "status", "--porcelain", "--", "qml"])
            if status.strip():
                raise RuntimeError("Coordinator QML has unreceipted local edits; preserved")
        # Only top-level hidden entries are ignored by Omarchy's recursive
        # watcher. A hidden directory INSIDE core still reloads cogitator-rite
        # for every copy/delete, even when its final contents are unchanged.
        stage = Path(tempfile.mkdtemp(prefix=".cogitator-runtime-", dir=self.plugins))
        try:
            shutil.copytree(source, stage, dirs_exist_ok=True)
            runpy.run_path(str(ROOT / "scripts/frame-style.py"))["apply_core_frames"](stage, self.root)
            runpy.run_path(str(ROOT / "scripts/voice-style.py"))["apply_voice"](stage, self.root, core=True)
            if file_hashes(stage) == file_hashes(target):
                return
            target.rename(Path(journal["backup"]) / f"coordinator-qml-{time.time_ns()}")
            stage.rename(target)
            atomic_write(receipt, json_bytes({"files": file_hashes(target)}))
        finally:
            if stage.exists():
                shutil.rmtree(stage)

    def disable(self):
        if not self.journal.exists():
            print("Suite already inactive.")
            return
        journal = json.loads(self.journal.read_text())
        if journal["phase"] == "restored":
            return
        current_raw = self.config.read_bytes() if self.config.exists() else None
        if current_raw is not None:
            atomic_write(Path(journal["backup"]) / f"shell-before-restore-{time.time_ns()}.json", current_raw)
        current = json.loads(current_raw) if current_raw is not None else journal["before"]
        if journal["phase"] in ("active", "switching"):
            restored = rollback_config(journal["before"], journal["applied"], current)
        else:
            # Failed before switching: restore the prepare baseline, including
            # undoing coordinator registration, while retaining other edits.
            expected = copy.deepcopy(journal["before"])
            expected.setdefault("plugins", []).append({"id": "cogitator-rite"})
            restored = rollback_config(journal["before"], expected, current)
        if restored == journal["before"]:
            if journal["originalBytes"] is None:
                self.config.unlink(missing_ok=True)
            else:
                atomic_write(self.config, base64.b64decode(journal["originalBytes"]), journal["originalMode"])
        else:
            atomic_write(self.config, json_bytes(restored), journal["originalMode"])
        journal["phase"] = "restored"
        journal["restoreInput"] = current
        journal["restoredConfig"] = restored
        journal["preservedEngagedEdits"] = restored != journal["before"]
        self.save(journal)
        print("Suite routes restored; recovery backups retained.")

    def finish(self):
        if not self.journal.exists():
            return
        journal = json.loads(self.journal.read_text())
        if journal["phase"] != "restored":
            raise RuntimeError("Cannot finish an unrestored suite")
        atomic_write(Path(journal["backup"]) / "suite-journal.json", json_bytes(journal))
        self.journal.unlink()

    def uninstall(self):
        if self.journal.exists():
            raise RuntimeError("Restore the suite before uninstalling it")
        for plugin in self.baselines:
            target = self.plugins / plugin["replacementId"]
            if not target.exists():
                continue
            receipt = target / RECEIPT
            if target.is_symlink() or not receipt.is_file() or json.loads(receipt.read_text()).get("files") != file_hashes(target):
                raise RuntimeError(f"Locally edited or foreign plugin preserved: {target}")
            self.run(["omarchy", "plugin", "remove", plugin["replacementId"], "--yes"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "enable", "refresh", "disable", "finish", "status", "uninstall"])
    parser.add_argument("--with-rite", action="store_true")
    args = parser.parse_args()
    suite = Suite()
    if args.action == "prepare":
        suite.prepare(args.with_rite)
    elif args.action == "status":
        print(suite.journal.read_text() if suite.journal.exists() else '{"phase":"inactive"}')
    else:
        getattr(suite, args.action)()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError, OSError, ValueError) as error:
        raise SystemExit(f"Cogitator suite: {error}")
