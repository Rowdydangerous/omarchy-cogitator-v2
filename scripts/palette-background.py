#!/usr/bin/env python3
"""Keep independent background selections for Cogitator palettes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time

PALETTES = ("green", "amber", "red", "industrial")
ROOT = Path(__file__).resolve().parents[1]


def state_home():
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))


def default_background(palette, theme_dir):
    folder = Path(theme_dir) / "backgrounds"
    if palette in PALETTES:
        filename = json.loads((ROOT / "palettes" / f"{palette}.json").read_text()).get("defaultWallpaper", "")
        if filename and Path(filename).name == filename and (folder / filename).is_file():
            return folder / filename
    return folder / f"cogitator-{palette}-grid.png"


def directory():
    return state_home() / "cogitator-v2/palette-backgrounds"


def remember(palette, image, folder=None):
    if palette not in (*PALETTES, "custom") or not image:
        return
    image = Path(image).resolve()
    if not image.is_file():
        return
    data = image.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    folder = Path(folder) if folder is not None else directory()
    cache = folder / palette / (digest + image.suffix.lower())
    cache.parent.mkdir(parents=True, exist_ok=True)
    # Preserve the selected image even if a theme reinstall removes its file.
    if not cache.exists():
        with cache.open("xb") as handle:
            handle.write(data)
    elif hashlib.sha256(cache.read_bytes()).hexdigest() != digest:
        raise ValueError(f"Saved background copy differs; preserved: {cache}")
    record = folder / f"{palette}.json"
    raw = json.dumps({"version": 1, "image": str(cache), "sha256": digest}, indent=2) + "\n"
    if record.exists():
        previous = record.read_text()
        if previous == raw:
            return
        history = folder / "history"
        history.mkdir(exist_ok=True)
        (history / f"{palette}-{time.time_ns()}.json").write_text(previous)
    with tempfile.NamedTemporaryFile(mode="w", dir=folder, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(raw)
    try:
        os.replace(temporary, record)
    finally:
        temporary.unlink(missing_ok=True)


def remember_current():
    current = state_home() / "omarchy/current"
    theme = (current / "theme.name").read_text().strip() if (current / "theme.name").is_file() else ""
    if theme.startswith("cogitator-"):
        remember(theme.removeprefix("cogitator-"), current / "background")


def selected_background(palette, theme_dir, folder=None):
    if palette not in (*PALETTES, "custom"):
        raise ValueError("Unknown palette")
    folder = Path(folder) if folder is not None else directory()
    record = folder / f"{palette}.json"
    if record.is_file():
        # Fail visibly rather than silently discard an invalid saved choice.
        data = json.loads(record.read_text())
        if data.get("version") != 1:
            raise ValueError(f"Unknown saved background format: {record}")
        image = Path(data["image"])
        if image.is_file():
            if hashlib.sha256(image.read_bytes()).hexdigest() != data["sha256"]:
                raise ValueError(f"Saved background copy differs; preserved: {image}")
            return image
    return default_background(palette, theme_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("remember")
    select = commands.add_parser("select")
    select.add_argument("palette", choices=(*PALETTES, "custom"))
    select.add_argument("theme_dir", type=Path)
    args = parser.parse_args()
    if args.command == "remember":
        remember_current()
    else:
        print(selected_background(args.palette, args.theme_dir))
