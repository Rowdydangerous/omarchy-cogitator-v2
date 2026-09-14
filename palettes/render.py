#!/usr/bin/env python3
"""Render Omarchy theme files from a centralized palette definition.

Usage: render.py <palette> [--check]
  Reads palettes/<palette>.json, writes repo-root colors.toml and shell.toml
  deterministically. The root doubles as a native Omarchy theme directory
  (colors.toml + shell.toml + backgrounds/ + icons.theme) and as a native
  plugin directory (manifest.json + qml/).
  --check verifies committed files match instead of writing.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

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


def darken(hexcolor, factor):
    hexcolor = hexcolor.lstrip("#")
    r, g, b = (int(hexcolor[i : i + 2], 16) for i in (0, 2, 4))
    r = round(r * factor)
    g = round(g * factor)
    b = round(b * factor)
    return "#{:02x}{:02x}{:02x}".format(r, g, b)


def main():
    check = "--check" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        print("Usage: render.py <palette> [--check]", file=sys.stderr)
        return 2
    name = args[0]
    pal_path = ROOT / "palettes" / f"{name}.json"
    palette = json.loads(pal_path.read_text())
    required = ["background", "surface", "inactive", "dim", "normal",
                "active", "highlight", "warning", "critical"]
    for key in required:
        if key not in palette:
            print(f"palette {name} missing key: {key}", file=sys.stderr)
            return 1
    ctx = dict(palette)
    ctx["palette"] = name
    ctx["dark_background"] = darken(palette["background"], 0.7)
    ctx["darker_background"] = darken(palette["background"], 0.45)

    if name != "green":
        print(f"prototype ships green only (asked: {name})", file=sys.stderr)
        return 1
    colors = COLORS_TEMPLATE.format(**ctx)
    shell = SHELL_TEMPLATE.format(**ctx)

    targets = {
        ROOT / "colors.toml": colors,
        ROOT / "shell.toml": shell,
    }
    failed = False
    for path, content in targets.items():
        if check:
            if not path.is_file() or path.read_text() != content:
                print(f"STALE: {path.relative_to(ROOT)}", file=sys.stderr)
                failed = True
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            print(f"wrote {path.relative_to(ROOT)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
