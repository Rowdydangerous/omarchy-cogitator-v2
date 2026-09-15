#!/usr/bin/env python3
"""Render Omarchy theme files from centralized palette definitions.

Usage:
  render.py [name ...] [--check] [--phosphor HEX]

  Reads palettes/<name>.json and writes deterministic theme files. The
  green flagship renders to the repo root (which doubles as a native
  plugin root AND native theme root); every other palette renders to
  themes/cogitator-<name>/ (with icons.theme + backgrounds/).

  render.py with no names renders every palettes/*.json file.
  render.py custom --phosphor '#7CFF6B' derives a one-off custom palette.

  --check verifies committed TOML files match instead of writing.
  Background PNGs are build artifacts regenerated on render, not checked.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ["background", "surface", "inactive", "dim", "normal",
            "active", "highlight", "warning", "critical"]


def clamp_channel(value):
    return max(0, min(255, int(round(value))))


def hex_to_rgb(hexcolor):
    hexcolor = hexcolor.lstrip("#")
    return tuple(int(hexcolor[i:i + 2], 16) for i in (0, 2, 4))


def fmt(rgb):
    return "#{:02x}{:02x}{:02x}".format(*(clamp_channel(c) for c in rgb))


def shade(hexcolor, factor):
    return fmt([c * factor for c in hex_to_rgb(hexcolor)])


def lighten(hexcolor, amount):
    return fmt([c + (255 - c) * amount for c in hex_to_rgb(hexcolor)])


def darken(hexcolor, factor):
    return shade(hexcolor, factor)


def custom_palette(phosphor):
    phosphor = phosphor.strip()
    if len(phosphor) == 4 and phosphor.startswith("#"):
        phosphor = "#" + "".join(c * 2 for c in phosphor[1:])
    hex_to_rgb(phosphor)  # validates shape
    if len(phosphor) != 7 or not phosphor.startswith("#"):
        raise ValueError("phosphor must be #RGB or #RRGGBB")
    return {
        "name": "custom",
        "description": f"User phosphor {phosphor}, derived scales.",
        "background": darken(phosphor, 0.06),
        "surface": darken(phosphor, 0.13),
        "inactive": darken(phosphor, 0.30),
        "dim": darken(phosphor, 0.48),
        "normal": phosphor,
        "active": lighten(phosphor, 0.28),
        "highlight": lighten(phosphor, 0.60),
        "warning": "#e0ad2f",
        "critical": "#ff5345",
        "customPhosphor": phosphor,
    }


SHELL_TEMPLATE = """# Omarchy shell surfaces for cogitator-{palette}.
# GENERATED from palettes/{palette}.json — do not hand-edit, run palettes/render.py.
# Sizes/spacing mirror stock defaults; only color tokens are phosphor-derived.

[bar]
background       = "{background}"
background-alpha = 1.0
text             = "{normal}"
active           = "{critical}"
scale-with-font  = true
size-horizontal  = 26
size-vertical    = 28

[hyprland]
active-border            = "{dim}"
active-border-foreground = "{normal}"

[controls]
normal-color        = "{normal}"
normal-fill-alpha   = 0.04
normal-border       = "{normal}"
normal-border-width = 1
normal-border-alpha = 0.4
hover-cursor-color        = "{active}"
hover-cursor-fill-alpha   = 0.08
hover-cursor-border       = "{active}"
hover-cursor-border-width = 1
hover-cursor-border-alpha = 0.35
focus-color        = "{active}"
focus-fill-alpha   = 0.08
focus-border       = "{active}"
focus-border-width = 1
focus-border-alpha = 0.35
selected-color        = "{active}"
selected-fill-alpha   = 0.18
selected-border       = "{active}"
selected-border-width = 0
selected-border-alpha = 1.0
pressed-fill-alpha   = 0.22
selection-fill-alpha = 0.35

[spacing]
scale = 1.0
scale-with-font = true

[font]
base-size = 12

[popups]
background       = "{background}"
background-alpha = 0.97
text             = "{normal}"
border           = "hyprland.active-border"
border-alpha     = 1.0

[tooltip]
background       = "{surface}"
background-alpha = 0.97
text             = "{highlight}"
border           = "hyprland.active-border-foreground"
border-alpha     = 1.0

[notifications]
background       = "{background}"
background-alpha = 0.97
text             = "{normal}"
border           = "hyprland.active-border"
border-alpha     = 1.0
countdown        = "{active}"

[launcher]
background                = "{background}"
background-alpha          = 0.94
text                      = "{normal}"
border                    = "hyprland.active-border-foreground"
border-alpha              = 1.0
scrim                     = "{background}"
scrim-alpha               = 0.55
selected-background       = "{normal}"
selected-background-alpha = 0.12
selected-text             = "{highlight}"
selected-border           = "hyprland.active-border-foreground"
selected-border-alpha     = 0.4

[menu]
background                = "{background}"
background-alpha          = 0.97
text                      = "{normal}"
border                    = "hyprland.active-border-foreground"
border-alpha              = 1.0
scrim                     = "{background}"
scrim-alpha               = 0.55
selected-background       = "{normal}"
selected-background-alpha = 0.12
selected-text             = "{highlight}"
selected-border           = "hyprland.active-border-foreground"
selected-border-alpha     = 0.4

[polkit]
background       = "{background}"
background-alpha = 1.0
text             = "{normal}"
text-error       = "{critical}"
border           = "hyprland.active-border"
border-error     = "{critical}"
border-alpha     = 1.0
scrim            = "{background}"
scrim-alpha      = 0.6
accent           = "{active}"

[lock]
background       = "{background}"
background-alpha = 0.85
text             = "{normal}"
placeholder      = "{dim}"
text-error       = "{critical}"
border           = "hyprland.active-border"
border-active    = "hyprland.active-border"
border-error     = "{critical}"
border-alpha     = 1.0
selection        = "{active}"
selection-alpha  = 0.45

[image-picker]
scrim                   = "{background}"
scrim-alpha             = 0.55
text                    = "{normal}"
selected-border         = "{active}"
selected-border-alpha   = 1.0
unselected-border       = "{normal}"
unselected-border-alpha = 0.28
"""

COLORS_TEMPLATE = """mode = "dark"

# GENERATED from palettes/{palette}.json — do not hand-edit, run palettes/render.py.
accent = "{normal}"
selection = "{inactive}"
muted = "{dim}"

background = "{background}"
dark_background = "{dark_background}"
darker_background = "{darker_background}"
lighter_background = "{surface}"

foreground = "{normal}"
dark_foreground = "{dim}"
light_foreground = "{active}"
bright_foreground = "{highlight}"

red = "{critical}"
yellow = "{warning}"
orange = "{warning}"
green = "{normal}"
cyan = "{active}"
blue = "{normal}"
magenta = "{active}"
brown = "{inactive}"

bright_red = "{critical}"
bright_yellow = "{warning}"
bright_green = "{active}"
bright_cyan = "{highlight}"
bright_blue = "{active}"
bright_magenta = "{highlight}"
"""


def rgba(hexcolor, alpha):
    r, g, b = hex_to_rgb(hexcolor)
    return f"rgba({r},{g},{b},{alpha})"


def render_background(palette, out_path):
    magick = shutil.which("magick") or shutil.which("convert")
    if not magick:
        print("magick not found; skipping background", file=sys.stderr)
        return
    normal = palette["normal"]
    subprocess.run([
        magick, "-size", "1920x1080", f"xc:{palette['background']}",
        "(", "-size", "120x120", "xc:none",
        "-fill", "none", "-stroke", rgba(normal, 0.10),
        "-strokewidth", "1", "-draw", "rectangle 0,0 119,119",
        "-write", "mpr:tile", "+delete", ")",
        "-tile", "mpr:tile", "-draw", "color 0,0 reset",
        "(", "-size", "1920x1080",
        "radial-gradient:rgba(0,0,0,0)-rgba(0,0,0,0.55)",
        "-fill", palette["surface"], "-opaque", "black",
        "+transparent", "black", ")",
        "-compose", "multiply", "-composite",
        "-fill", rgba(normal, 0.05),
        "-draw", "circle 960,470 960,220",
        str(out_path),
    ], check=True)
    print(f"wrote {out_path.relative_to(ROOT)}")


def load_palette(name, phosphor):
    if name == "custom":
        if not phosphor:
            print("custom needs --phosphor HEX", file=sys.stderr)
            sys.exit(1)
        return custom_palette(phosphor)
    pal_path = ROOT / "palettes" / f"{name}.json"
    palette = json.loads(pal_path.read_text())
    for key in REQUIRED:
        if key not in palette:
            print(f"palette {name} missing key: {key}", file=sys.stderr)
            sys.exit(1)
    return palette


def render_one(name, palette, check):
    ctx = dict(palette)
    ctx["palette"] = "custom phosphor" if name == "custom" else name
    ctx["dark_background"] = darken(palette["background"], 0.7)
    ctx["darker_background"] = darken(palette["background"], 0.45)
    if name == "green":
        theme_dir = ROOT
        png_name = "cogitator-green-grid.png"
    else:
        theme_dir = ROOT / "themes" / f"cogitator-{name}"
        png_name = f"cogitator-{name}-grid.png"
    colors = COLORS_TEMPLATE.format(**ctx)
    shell = SHELL_TEMPLATE.format(**ctx)
    failed = False
    for rel, content in (("colors.toml", colors), ("shell.toml", shell)):
        path = theme_dir / rel
        if check:
            if not path.is_file() or path.read_text() != content:
                print(f"STALE: {path.relative_to(ROOT)}", file=sys.stderr)
                failed = True
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            print(f"wrote {path.relative_to(ROOT)}")
    if name != "green" and not check:
        (theme_dir / "icons.theme").write_text("Yaru-sage\n")
    if not check:
        bg_dir = theme_dir / "backgrounds"
        bg_dir.mkdir(parents=True, exist_ok=True)
        render_background(palette, bg_dir / png_name)
    return failed


def main():
    check = "--check" in sys.argv
    phosphor = None
    if "--phosphor" in sys.argv:
        phosphor = sys.argv[sys.argv.index("--phosphor") + 1]
    skip = {"--check", "--phosphor"}
    if phosphor is not None:
        skip.add(phosphor)
    tokens = [a for a in sys.argv[1:] if a not in skip and not a.startswith("--")]
    if not tokens:
        tokens = sorted(p.stem for p in (ROOT / "palettes").glob("*.json"))
    failed = False
    for name in tokens:
        palette = load_palette(name, phosphor)
        if render_one(name, palette, check):
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
