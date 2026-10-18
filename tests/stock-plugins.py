#!/usr/bin/env python3
"""Validate baseline completeness, identities and native manifest contracts."""
import hashlib
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
baseline = json.loads((root / "docs/stock-baseline.json").read_text())
ids = set()
for plugin in baseline["plugins"]:
    directory = root / plugin["path"]
    manifest = json.loads((directory / "manifest.json").read_text())
    assert manifest["id"] == plugin["replacementId"]
    assert manifest["id"] not in ids
    ids.add(manifest["id"])
    assert manifest["omarchy"]["clonedFrom"] == plugin["sourceId"]
    for entry in manifest["entryPoints"].values():
        assert (directory / entry).is_file(), (directory, entry)
    for file, digest in plugin["baselineFiles"].items():
        if file == "manifest.json":
            continue  # Local identity intentionally differs from stock.
        path = directory / file
        assert path.is_file(), path
        if plugin["status"] == "stock-baseline":
            content = path.read_bytes()
            for relocation in plugin.get("cloneRelocations", []):
                if path.suffix in (".qml", ".js", ".json"):
                    # Undo only relocated URL literals for source provenance.
                    content = content.replace(('"' + relocation["target"] + '/').encode(),
                                              ('"' + relocation["source"] + '/').encode())
            assert hashlib.sha256(content).hexdigest() == digest, path
    subprocess.run(["omarchy", "plugin", "validate", str(directory)],
                   check=True, stdout=subprocess.DEVNULL)
assert (root / "plugins/indicators/indicators/Dnd.qml").is_file()
assert 'Qt.resolvedUrl("indicators/"' in (root / "plugins/indicators/Indicators.qml").read_text()
print(f"Validated {len(ids)} complete stock-based plugins.")
