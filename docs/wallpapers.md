# Cogitator wallpaper renderer

`scripts/render-wallpaper.py` turns local artwork into a static phosphor wallpaper
with soft bloom, scanlines, deterministic grain, a chamfered frame, and captions.
It writes a PNG and a `-preview.png` (beside it by default, or in `--preview-dir`).
It never applies the wallpaper and
refuses to overwrite existing outputs or the source. Output directories must
already exist. Original source inputs remain separate from rendered wallpapers.

## Folder layout

| Palette | Full-resolution wallpapers | Review previews |
| --- | --- | --- |
| Green | `backgrounds/` | `docs/wallpaper-previews/green/` |
| Amber | `themes/cogitator-amber/backgrounds/` | `docs/wallpaper-previews/amber/` |
| Red | `themes/cogitator-red/backgrounds/` | `docs/wallpaper-previews/red/` |
| Industrial | `themes/cogitator-industrial/backgrounds/` | `docs/wallpaper-previews/industrial/` |
| Custom | `themes/cogitator-custom/backgrounds/` | `docs/wallpaper-previews/custom/` |

Green's root location preserves native theme installation. Custom theme files
are generated on palette selection. Use `--preview-dir` to keep review images
out of selectable wallpaper folders; Omarchy treats every PNG there as a
wallpaper, not as a thumbnail for another file.

For rendering and copying wallpapers into an already-installed theme's user
background directory, see [the README walkthrough](../README.md#make-your-own-background).

## Requirements

Python 3, Pillow, and NumPy. On the development Omarchy machine use
`/usr/bin/python3`; the separate mise Python does not have the image libraries.
The renderer uses Monaspace Xenon Frozen when installed, with a Pillow font
fallback. `--font /path/to/font.ttf` selects another font for this image only.

## Choose an extraction mode

| Mode | Best for |
| --- | --- |
| `image` (default) | Complete pictures, inscriptions, and mixed-color artwork. Uses luminance. |
| `gold` | Gold emblems on neutral backgrounds; uses the original Aquila chroma extraction. |
| `green` | Green emblems on neutral backgrounds. |
| `saturation` | Colored foregrounds on grayscale backgrounds. |

Use `--invert` for dark artwork on a pale background. `--gamma 1.6` suppresses
faint background detail; values below 1 bring it out. `--brightness 1.3` increases
phosphor intensity. Extraction modes crop to the detected foreground; `image`
preserves the entire composition. All modes retain aspect ratio inside a
centered area up to 78% of canvas width and 64% of canvas height.

### Full-image example: wings and banner

From the repository root:

```bash
/usr/bin/python3 scripts/render-wallpaper.py \
  "$HOME/Downloads/Cog_background/and_they_shall_know_no_fear.jpg" \
  "$HOME/Pictures/Wallpapers/cogitator-no-fear-2560x1600.png" \
  --preview-dir docs/wallpaper-previews/green \
  --mode image --invert --gamma 1.6 --brightness 1.3 \
  --title "IMPERIAL ARCHIVE  //  AND THEY SHALL KNOW NO FEAR" \
  --no-grid
```

The input already has a tile pattern, so the additional schematic grid is
disabled. Inverting the luminance keeps both the dark wings and banner lettering
readable against a near-black field.

### Gold emblem example

```bash
/usr/bin/python3 scripts/render-wallpaper.py \
  "$HOME/Downloads/Cog_background/yellow_eagle.jpg" \
  "$HOME/Pictures/Wallpapers/cogitator-aquila-renderer.png" \
  --preview-dir docs/wallpaper-previews/green \
  --mode gold --title "IMPERIAL ARCHIVE  //  AQUILA" \
  --caption "AUTHORITY SEAL  /  LOCAL COGITATOR"
```

This uses the original gold mask and phosphor treatment, with the generalized
renderer's centered, resolution-relative layout.

## Other controls

- `--size 3840x2160` changes canvas dimensions (default `2560x1600`).
- `--phosphor '#e0ad2f' --background '#080603'` selects custom RGB colors.
- `--title`, `--caption`, and `--motto` change the three captions; pass `""` to hide one.
- `--no-grid` and `--no-frame` hide those decorations independently.
- `--seed 40000` controls reproducible grain.
- `--preview-dir /existing/folder` stores the review PNG separately from the wallpaper.
- `--help` lists all options.

Review the preview before applying. To apply the generated full-resolution file:

```bash
omarchy theme bg set "$HOME/Pictures/Wallpapers/cogitator-no-fear-2560x1600.png"
```
