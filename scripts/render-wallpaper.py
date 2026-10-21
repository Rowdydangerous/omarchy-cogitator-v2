#!/usr/bin/python3
"""Render an image as a static Cogitator wallpaper (Pillow + NumPy)."""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


def dimensions(value):
    try:
        width, height = map(int, value.lower().split("x"))
        if min(width, height) < 320:
            raise ValueError
        return width, height
    except ValueError:
        raise argparse.ArgumentTypeError("expected WIDTHxHEIGHT, both at least 320")


def positive(value):
    number = float(value)
    if not np.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("expected a finite positive number")
    return number


def color(value):
    try:
        value = value.removeprefix("#")
        if len(value) != 6:
            raise ValueError
        return np.array([int(value[i:i + 2], 16) for i in (0, 2, 4)])
    except ValueError:
        raise argparse.ArgumentTypeError("expected a six-digit RGB hex color")


def extract(image, mode, invert, gamma):
    rgb = np.asarray(image, dtype=np.float32) / 255
    r, g, b = rgb.transpose(2, 0, 1)
    if mode == "gold":
        signal = np.clip((np.minimum(r, g) - b - .025) / .55, 0, 1)
    elif mode == "green":
        signal = np.clip((g - np.maximum(r, b) - .015) / .28, 0, 1)
    elif mode == "saturation":
        signal = np.clip((rgb.max(axis=2) - rgb.min(axis=2)) / .5, 0, 1)
    else:
        signal = .2126 * r + .7152 * g + .0722 * b
    if invert:
        signal = 1 - signal
    return Image.fromarray(np.uint8(np.clip(signal, 0, 1) ** gamma * 255))


def render(args):
    width, height = args.size
    scale = min(width / 2560, height / 1600)
    with Image.open(args.source) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        # Composite transparent artwork onto neutral black before extraction.
        if "A" in source.getbands() or "transparency" in source.info:
            rgba = ImageOps.exif_transpose(source).convert("RGBA")
            background = Image.new("RGBA", rgba.size, "black")
            image = Image.alpha_composite(background, rgba).convert("RGB")
    mask = extract(image, args.mode, args.invert, args.gamma)
    if args.mode != "image":
        box = mask.point(lambda value: 255 if value > 30 else 0).getbbox()
        if box is None:
            raise ValueError("no foreground found; try --mode image or another extraction mode")
        mask = mask.crop(box)
    mask = ImageOps.contain(mask, (int(width * .78), int(height * .64)),
                            Image.Resampling.LANCZOS)
    full = Image.new("L", (width, height))
    full.paste(mask, ((width - mask.width) // 2, (height - mask.height) // 2))
    core = np.asarray(full, dtype=np.float32) / 255
    narrow = np.asarray(full.filter(ImageFilter.GaussianBlur(3 * scale)), dtype=np.float32) / 255
    wide = np.asarray(full.filter(ImageFilter.GaussianBlur(20 * scale)), dtype=np.float32) / 255
    edge = np.clip(core - np.asarray(full.filter(ImageFilter.MinFilter(3)), dtype=np.float32) / 255, 0, 1)
    yy, xx = np.mgrid[0:height, 0:width]
    radius = ((xx - width * .48) / (width * .70)) ** 2 + ((yy - height * .47) / (height * .85)) ** 2
    vignette = np.clip(1 - .65 * radius, .25, 1)
    base = np.empty((height, width, 3), dtype=np.float32)
    base[:] = args.background
    tint = args.phosphor / 255
    base += (np.exp(-radius * 3) * 3)[:, :, None] * tint
    base += np.random.default_rng(args.seed).normal(0, .3, (height, width))[:, :, None]
    light = .77 * core + .13 * narrow + .10 * wide + .10 * edge
    scanlines = np.where(yy % max(2, round(3 * scale)) == 0, .78, 1)
    base += (light * scanlines * vignette * args.brightness)[:, :, None] * args.phosphor * .615
    art = Image.fromarray(np.uint8(np.clip(base, 0, 255)))
    draw = ImageDraw.Draw(art)

    def point(x, y):
        return round(x * width / 2560), round(y * height / 1600)

    def ink(factor):
        return tuple(int(channel * factor) for channel in args.phosphor)

    if not args.no_grid:
        for x in range(64, 2528, 96):
            draw.line([point(x, 64), point(x, 1536)], fill=ink(.065))
        for y in range(64, 1568, 96):
            draw.line([point(64, y), point(2496, y)], fill=ink(.065))
    if not args.no_frame:
        draw.line([point(x, y) for x, y in [(64, 80), (2496, 80), (2496, 1494),
                  (2454, 1536), (64, 1536), (64, 80)]], fill=ink(.17), width=max(1, round(2 * scale)))
        for x, y, sx, sy in [(58, 74, 1, 1), (2502, 74, -1, 1), (58, 1542, 1, -1)]:
            draw.line([point(x, y + 30 * sy), point(x, y), point(x + 30 * sx, y)],
                      fill=ink(.33), width=max(1, round(3 * scale)))
    try:
        font = ImageFont.truetype(str(args.font), max(8, round(17 * scale)))
        small = ImageFont.truetype(str(args.font), max(8, round(14 * scale)))
    except OSError:
        font = ImageFont.load_default(size=max(8, round(17 * scale)))
        small = ImageFont.load_default(size=max(8, round(14 * scale)))
    draw.text(point(92, 104), args.title, font=font, fill=ink(.31))
    draw.text(point(92, 1488), args.caption, font=small, fill=ink(.24))
    label_width = draw.textlength(args.motto, font=small)
    draw.text((point(2466, 1488)[0] - label_width, point(2466, 1488)[1]),
              args.motto, font=small, fill=ink(.24))
    return art


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path, help="new PNG output path (parent must exist)")
    parser.add_argument("--preview-dir", type=Path,
                        help="existing directory for the preview (default: beside output)")
    parser.add_argument("--mode", choices=("image", "gold", "green", "saturation"), default="image",
                        help="full-image luminance or foreground color extraction (default: image)")
    parser.add_argument("--invert", action="store_true", help="use for dark artwork on a light background")
    parser.add_argument("--gamma", type=positive, default=1, help=">1 suppresses faint details")
    parser.add_argument("--brightness", type=positive, default=1)
    parser.add_argument("--size", type=dimensions, default=(2560, 1600))
    parser.add_argument("--phosphor", type=color, default=color("4fd06a"))
    parser.add_argument("--background", type=color, default=color("030704"))
    parser.add_argument("--title", default="IMPERIAL ARCHIVE  //  IMAGE RECORD")
    parser.add_argument("--caption", default="LOCAL COGITATOR  /  ARCHIVE RECORD")
    parser.add_argument("--motto", default="+++ THE MACHINE ENDURES +++")
    parser.add_argument("--font", type=Path, default=Path("/usr/share/fonts/TTF/MonaspaceXenonFrozen-Regular.ttf"))
    parser.add_argument("--seed", type=int, default=40_000)
    parser.add_argument("--no-grid", action="store_true")
    parser.add_argument("--no-frame", action="store_true")
    args = parser.parse_args()
    if args.output.is_dir():
        parser.error("output is a directory; provide a filename such as "
                     f"{args.output / 'cogitator-wallpaper.png'}")
    preview = args.output.with_name(args.output.stem + "-preview.png")
    if args.preview_dir is not None:
        preview = args.preview_dir / preview.name
    for path in (args.output, preview):
        if path.resolve() == args.source.resolve() or path.exists():
            parser.error(f"refusing to overwrite: {path}")
        if not path.parent.is_dir():
            parser.error(f"output directory does not exist: {path.parent}")
    if args.output.suffix.lower() != ".png":
        parser.error("output must have a .png extension")
    try:
        art = render(args)
        # Exclusive creation also guards against another invocation taking the path.
        with args.output.open("xb") as output:
            art.save(output, format="PNG", optimize=True)
        art.thumbnail((1280, 800), Image.Resampling.LANCZOS)
        with preview.open("xb") as output:
            art.save(output, format="PNG", optimize=True)
    except (OSError, ValueError) as error:
        parser.exit(1, f"render failed: {error}\n")
    print(f"Wallpaper: {args.output}\nPreview: {preview}")


if __name__ == "__main__":
    main()
