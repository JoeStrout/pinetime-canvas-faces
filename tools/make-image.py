#!/usr/bin/env python3
"""Convert a picture to an LVGL .bin image for a Canvas face, resizing it to fit.

    tools/make-image.py couple.png faces/tango/couple.bin --height 240

Give --width, --height or both; the aspect ratio is kept, so the picture fits inside
the size given. Needs Pillow.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image

import lvimage


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("image", help="source picture")
    parser.add_argument("output", help=".bin file to write")
    parser.add_argument("--width", type=int, help="fit within this width")
    parser.add_argument("--height", type=int, help="fit within this height")
    parser.add_argument("--format", choices=lvimage.FORMATS, default="indexed4",
                        help="indexed4: 16 colors, smallest (default); indexed8: 256 colors; "
                             "truecolor: full color with alpha, largest")
    parser.add_argument("--preview", help="also write a PNG of the result as the watch will show it")
    args = parser.parse_args()

    img = Image.open(args.image).convert("RGBA")
    scale = min(args.width / img.width if args.width else float("inf"),
                args.height / img.height if args.height else float("inf"))
    if scale != float("inf"):
        size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
        # Resize premultiplied, so transparent pixels don't bleed dark edges into the picture
        img = img.convert("RGBa").resize(size, Image.Resampling.LANCZOS).convert("RGBA")

    data = lvimage.encode(img, args.format)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    if args.preview:
        shown = img.quantize(colors=16 if args.format == "indexed4" else 256, method=Image.Quantize.FASTOCTREE) \
            if args.format != "truecolor" else img
        shown.convert("RGBA").save(args.preview)

    print(f"wrote {output}: {img.width}x{img.height} px, {len(data) / 1024:.1f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
