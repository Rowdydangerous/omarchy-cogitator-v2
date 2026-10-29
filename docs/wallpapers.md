# Cogitator wallpaper renderer

`scripts/render-wallpaper.py` turns local artwork into a static phosphor wallpaper
with soft bloom, scanlines, deterministic grain, a chamfered frame, and captions.
By default it generates **four variants** using the project's exact palette
definitions: Imperium, Ryza, Holy Mars, and Metalica. It never applies the wallpaper
or overwrites existing outputs/source images. Output directories are created.

## Generate a matching set

```bash
/usr/bin/python3 scripts/render-wallpaper.py /path/to/artwork.jpg
```

The default filename is `cogitator-artwork-2560x1600.png`, written under each of:

```text
~/.config/omarchy/backgrounds/cogitator-green/
~/.config/omarchy/backgrounds/cogitator-amber/
~/.config/omarchy/backgrounds/cogitator-red/
~/.config/omarchy/backgrounds/cogitator-industrial/
```

Preview PNGs go under `~/.cache/cogitator-v2/wallpaper-previews/<palette>/`, not
into the wallpaper selectors. XDG config/cache/state overrides are honored.
Generation does not change or link background selections. Choose whichever
image you want separately for each palette, using Omarchy's background selector
or `omarchy theme bg set <path>`.

Subsequent **Cogitator palette** changes remember the image of the palette you
are leaving and restore the destination palette's own background. Each palette
(including custom) is independent. The selected image is captured before
Omarchy's native theme operation can replace it; a saved copy under
`~/.local/state/cogitator-v2/palette-backgrounds/` protects it against theme
reinstalls and removed/moved source files. Disabling also remembers the current
choice so it can be restored on the next enable. This works through Cogitator's
controller and CLI; it does not install a hook for arbitrary native theme changes.

Packaged defaults are used only when a palette has no saved selection:

| Palette | Default artwork |
| --- | --- |
| Imperium | Aquila |
| Ryza | mechSkull3, amber |
| Holy Mars | mechSkull1, red |
| Metalica | mechSkull2, cream/brass |

The files are selected by `defaultWallpaper` in `palettes/*.json`. Each existing
grid remains available as an alternative (and as a fallback if an image is missing).

For another output location/name, pass a PNG base path:

```bash
/usr/bin/python3 scripts/render-wallpaper.py /path/to/artwork.jpg \
  "$HOME/Pictures/Wallpapers/my-seal.png"
```

This creates `Wallpapers/cogitator-<palette>/my-seal.png`. External outputs aren't
automatically added to Omarchy's selector folders: select each desired image
while its palette is active using `omarchy theme bg set <path>`. Existing
single-color images remain unchanged.

## Generate just one palette

```bash
/usr/bin/python3 scripts/render-wallpaper.py /path/to/artwork.jpg \
  "$HOME/Pictures/Wallpapers/one-ryza.png" --palette amber
```

With a single `--palette`, the optional output path is used **exactly**. Omit it
to write to that palette's user-background folder. Use internal IDs `green`,
`amber`, `red`, and `industrial`. Custom hex colors require single-palette mode.
`--preview-dir /path/to/previews` changes the preview root; all-mode adds palette
subfolders, while single-palette mode uses that directory directly.

Every target wallpaper/preview is checked before the first render: if any exists,
generation stops without overwriting it. A later I/O failure can leave partial
outputs; review the error and those new files before retrying with another name.

## Repository's packaged wallpaper layout

| Palette | Full-resolution wallpapers | Review previews |
| --- | --- | --- |
| Imperium (green) | `backgrounds/` | `docs/wallpaper-previews/green/` |
| Ryza (amber) | `themes/cogitator-amber/backgrounds/` | `docs/wallpaper-previews/amber/` |
| Holy Mars (red) | `themes/cogitator-red/backgrounds/` | `docs/wallpaper-previews/red/` |
| Metalica (industrial) | `themes/cogitator-industrial/backgrounds/` | `docs/wallpaper-previews/industrial/` |
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
  --mode gold --title "IMPERIAL ARCHIVE  //  AQUILA" \
  --caption "AUTHORITY SEAL  /  LOCAL COGITATOR"
```

This uses the original gold mask and phosphor treatment, with the generalized
renderer's centered, resolution-relative layout.

## Other controls

- `--size 3840x2160` changes canvas dimensions (default `2560x1600`).
- `--palette green --phosphor '#e0ad2f' --background '#080603'` selects custom RGB colors for a single output.
- `--title`, `--caption`, and `--motto` change the three captions; pass `""` to hide one.
- `--no-grid` and `--no-frame` hide those decorations independently.
- `--seed 40000` controls reproducible grain.
- `--preview-dir /path/to/previews` changes the separate preview root.
- `--help` lists all options.

Review the preview before applying. To apply the generated full-resolution file:

```bash
omarchy theme bg set "$HOME/.config/omarchy/backgrounds/cogitator-green/cogitator-and_they_shall_know_no_fear-2560x1600.png"
```
