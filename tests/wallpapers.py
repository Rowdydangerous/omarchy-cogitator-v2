#!/usr/bin/env python3
"""Palette wallpapers must stay opaque for the transparent bar's color picker.

Omarchy's omarchy-bar-text-color samples the top wallpaper strip with
ImageMagick `-extent`, which composites any alpha onto white. A semi-transparent
wallpaper therefore samples near-white, and the picker keeps the theme
background (near-black) instead of the phosphor foreground because black has
more contrast against white. The bar then paints every bar.barForeground
widget — glyphs, icons, clock text — in that near-black.

The grid wallpapers shipped as 16-bit RGBA with alpha 0.1, which is exactly the
case that triggers this. Keep the shipped palette wallpapers opaque. PNG headers
are read directly so this check has no image-library dependency.
"""
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WALLPAPERS = [
    ROOT / "backgrounds/cogitator-green-grid.png",
    ROOT / "themes/cogitator-amber/backgrounds/cogitator-amber-grid.png",
    ROOT / "themes/cogitator-red/backgrounds/cogitator-red-grid.png",
    ROOT / "themes/cogitator-industrial/backgrounds/cogitator-industrial-grid.png",
]
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
ALPHA_COLOR_TYPES = {4, 6}  # grayscale+alpha, truecolor+alpha


def png_has_alpha(path):
    """True when a PNG stores an alpha channel or a transparency chunk."""
    data = path.read_bytes()
    assert data[:8] == PNG_SIGNATURE, f"{path.name} is not a PNG"
    offset = 8
    color_type = None
    while offset + 8 <= len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        chunk = data[offset + 4:offset + 8]
        if chunk == b"IHDR":
            # width(4) height(4) bit-depth(1) color-type(1)
            color_type = data[offset + 17]
        elif chunk == b"tRNS":
            return True
        elif chunk == b"IEND":
            break
        offset += 12 + length
    assert color_type is not None, f"{path.name} has no IHDR chunk"
    return color_type in ALPHA_COLOR_TYPES


for path in WALLPAPERS:
    assert path.is_file(), f"missing palette wallpaper: {path.relative_to(ROOT)}"
    assert not png_has_alpha(path), (
        f"{path.relative_to(ROOT)} has an alpha channel; the transparent bar's "
        "contrast picker composites it onto white and the bar loses its palette color"
    )

print(f"{len(WALLPAPERS)} palette wallpapers are opaque")
