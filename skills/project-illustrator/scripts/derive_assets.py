# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow>=10"]
# ///
"""Derive social card, circular thumbnail, avatar and favicons from a master image.

Usage: uv run derive_assets.py MASTER OUT_DIR [--focus X,Y] [--only NAME ...]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

# name -> (width, height, circular)
TARGETS: dict[str, tuple[int, int, bool]] = {
    'social-card': (1200, 630, False),
    'thumbnail': (256, 256, True),
    'avatar': (512, 512, False),
    'favicon-32': (32, 32, False),
    'apple-touch-icon': (180, 180, False),
}


def crop_box(
    size: tuple[int, int],
    target: tuple[int, int],
    focus: tuple[float, float] = (0.5, 0.5),
) -> tuple[int, int, int, int]:
    """Largest target-aspect box centered on focus, clamped inside the image."""
    w, h = size
    tw, th = target
    cw, ch = (w, round(w * th / tw)) if w * th <= h * tw else (round(h * tw / th), h)
    left = min(max(round(focus[0] * w - cw / 2), 0), w - cw)
    top = min(max(round(focus[1] * h - ch / 2), 0), h - ch)
    return left, top, left + cw, top + ch


def circle_mask(size: int, scale: int = 4) -> Image.Image:
    big = Image.new('L', (size * scale, size * scale), 0)
    ImageDraw.Draw(big).ellipse((0, 0, size * scale - 1, size * scale - 1), fill=255)
    return big.resize((size, size), Image.LANCZOS)


def derive(
    img: Image.Image, name: str, focus: tuple[float, float] = (0.5, 0.5)
) -> tuple[Image.Image, str | None]:
    """Return (image, warning or None) for one named target."""
    tw, th, circular = TARGETS[name]
    box = crop_box(img.size, (tw, th), focus)
    region = img.crop(box)
    warning = None
    if region.width < tw or region.height < th:
        warning = f'{name}: crop is {region.width}x{region.height}, upscaled to {tw}x{th}'
    out = region.resize((tw, th), Image.LANCZOS).convert('RGBA')
    if circular:
        out.putalpha(circle_mask(tw))
    return out, warning


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('master', type=Path)
    p.add_argument('out_dir', type=Path)
    p.add_argument('--focus', default='0.5,0.5', help='focal point X,Y as 0-1 fractions')
    p.add_argument('--only', nargs='+', choices=TARGETS, help='derive only these targets')
    args = p.parse_args(argv)

    try:
        fx, fy = (float(v) for v in args.focus.split(','))
    except ValueError:
        p.error('--focus needs two fractions between 0 and 1, e.g. 0.4,0.5')
    if not (0 <= fx <= 1 and 0 <= fy <= 1):
        p.error('--focus needs two fractions between 0 and 1, e.g. 0.4,0.5')
    focus = (fx, fy)

    img = Image.open(args.master).convert('RGBA')
    args.out_dir.mkdir(parents=True, exist_ok=True)
    warned = False
    for name in args.only or TARGETS:
        out, warning = derive(img, name, focus)
        if warning:
            warned = True
            sys.stderr.write(f'WARNING: {warning}\n')
        path = args.out_dir / f'{name}.png'
        out.save(path)
        sys.stdout.write(f'{path} {out.width}x{out.height}\n')
    return 1 if warned else 0


if __name__ == '__main__':
    sys.exit(main())
