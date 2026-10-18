#!/usr/bin/env python3
"""Import installed Omarchy plugins as reviewable, non-activated baselines.

Run once against an installed Omarchy release. Existing destinations are never
overwritten: upstream updates must be reviewed rather than erase styling.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    catalog = json.loads(subprocess.check_output(["omarchy-plugin-catalog"], text=True))
    entries = sorted((p for p in catalog if p.get("firstParty")), key=lambda p: p["id"])
    destination = ROOT / "plugins"
    if destination.exists():
        raise SystemExit("plugins/ already exists; review upstream changes before reimporting")
    records = []
    for plugin in entries:
        source = Path(plugin["sourceDir"])
        manifest_path = Path(plugin["manifestPath"])
        manifest = json.loads(manifest_path.read_text())
        slug = plugin["id"].removeprefix("omarchy.")
        target = destination / slug
        relocations = []
        if manifest_path.name == "manifest.json":
            shutil.copytree(source, target, symlinks=False)
        else:
            target.mkdir(parents=True)
            copies = [(v, v) for v in manifest["entryPoints"].values()]
            copies += [(p["source"], p["target"]) for p in manifest.get("omarchy", {}).get("clonePaths", [])]
            relocations = [(src, dst) for src, dst in copies if src != dst]
            for src, dst in sorted(set(copies)):
                relative = Path(dst)
                if relative.is_absolute() or ".." in relative.parts:
                    raise ValueError(f"Unsafe clone destination: {dst}")
                output = target / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                if (source / src).is_dir():
                    shutil.copytree(source / src, output, symlinks=False)
                else:
                    shutil.copy2(source / src, output)
        # Record original bytes before changing the local manifest identity.
        hashes = {str(f.relative_to(target)): hashlib.sha256(f.read_bytes()).hexdigest()
                  for f in sorted(target.rglob("*")) if f.is_file()}
        # Rewrite after ALL files are copied: dependency directories may sort
        # before the entry point that references them.
        for src, dst in relocations:
            for file in target.rglob("*"):
                if file.is_file() and file.suffix in (".qml", ".js", ".json"):
                    file.write_text(file.read_text().replace(src, dst))
        manifest["id"] = f"cogitator.{slug}"
        manifest["name"] = f"Cogitator {manifest['name']}"
        manifest.setdefault("omarchy", {})["clonedFrom"] = plugin["id"]
        manifest["omarchy"].pop("clonePaths", None)
        if isinstance(manifest.get("barWidget"), dict):
            manifest["barWidget"]["displayName"] = manifest["name"]
        (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        records.append({"sourceId": plugin["id"], "replacementId": manifest["id"],
                        "path": f"plugins/{slug}", "status": "stock-baseline",
                        "sourceManifest": str(manifest_path), "sourceManifestSha256":
                        hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                        "baselineFiles": hashes, "cloneRelocations":
                        [{"source": src, "target": dst} for src, dst in relocations]})
    version = subprocess.check_output(["omarchy", "version"], text=True).strip()
    (ROOT / "docs" / "stock-baseline.json").write_text(json.dumps(
        {"omarchyVersion": version, "plugins": records}, indent=2) + "\n")
    print(f"Imported {len(records)} stock-based plugins; none activated.")


if __name__ == "__main__":
    main()
