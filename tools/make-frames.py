#!/usr/bin/env python3
"""Pre-render rotated frames of an image for a Canvas image hand.

Give it a picture drawn pointing straight up (towards 12 o'clock). It writes one LVGL
.bin image per angle, all the same square size and centred on the same point, which is
what `hand ... image=` expects:

    tools/make-frames.py glove.png faces/mickey --name glove --frames 60

    hand minute 0 0 240 240 radius=85 image=/canvas/mickey/glove{frame:02}.bin frames=60

The point that should sit at the end of the arm defaults to the centre of the picture;
use --center X,Y to choose another. Needs Pillow.
"""
import argparse
import math
import struct
import sys
from pathlib import Path

from PIL import Image

# LVGL 7 color formats (lv_img_cf_t)
CF_TRUE_COLOR_ALPHA = 5
CF_INDEXED_4BIT = 9


def header(cf: int, width: int, height: int) -> bytes:
    return struct.pack("<I", cf | (width << 10) | (height << 21))


def encode_true_color_alpha(img: Image.Image) -> bytes:
    """RGB565 with bytes swapped (LV_COLOR_16_SWAP), then 8-bit alpha: InfiniTime's ARGB8565_RBSWAP."""
    out = bytearray(header(CF_TRUE_COLOR_ALPHA, img.width, img.height))
    data = img.tobytes()
    for i in range(0, len(data), 4):
        r, g, b, a = data[i:i + 4]
        c16 = ((r * 31 + 127) // 255) << 11 | ((g * 63 + 127) // 255) << 5 | ((b * 31 + 127) // 255)
        out += bytes((c16 >> 8, c16 & 0xFF, a))
    return bytes(out)


def encode_indexed4(img: Image.Image) -> bytes:
    """16-color palette with alpha: about a sixth of the size of true color."""
    quantized = img.quantize(colors=16, method=Image.Quantize.FASTOCTREE)
    palette = quantized.getpalette(rawmode="RGBA") or []
    palette = (palette + [0] * 64)[:64]
    out = bytearray(header(CF_INDEXED_4BIT, img.width, img.height))
    for i in range(16):
        r, g, b, a = palette[i * 4:i * 4 + 4]
        out += bytes((b, g, r, a))  # lv_color32_t order
    pixels = list(quantized.tobytes())
    for y in range(img.height):
        row = pixels[y * img.width:(y + 1) * img.width]
        if len(row) % 2:
            row.append(0)
        out += bytes((row[i] << 4) | row[i + 1] for i in range(0, len(row), 2))
    return bytes(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("image", help="source picture, pointing up")
    parser.add_argument("outdir", help="face folder to write the frames into")
    parser.add_argument("--name", default="frame", help="file name prefix (default: frame)")
    parser.add_argument("--frames", type=int, default=60, help="number of angles (default: 60)")
    parser.add_argument("--center", help="X,Y in the picture that sits at the end of the arm (default: its centre)")
    parser.add_argument("--format", choices=["indexed4", "truecolor"], default="indexed4",
                        help="indexed4: 16 colors, small (default); truecolor: full color, ~6x larger")
    parser.add_argument("--preview", help="also write a PNG contact sheet of all frames")
    args = parser.parse_args()

    src = Image.open(args.image).convert("RGBA")
    if args.center:
        cx, cy = (float(v) for v in args.center.split(","))
    else:
        cx, cy = src.width / 2, src.height / 2

    # A square big enough for the picture at any angle, with the chosen point in the middle
    reach = max(math.hypot(x - cx, y - cy) for x in (0, src.width) for y in (0, src.height))
    size = 2 * math.ceil(reach) + 2
    canvas = Image.new("RGBA", (size, size))
    canvas.paste(src, (round(size / 2 - cx), round(size / 2 - cy)))
    # Rotate premultiplied, so transparent pixels don't bleed dark edges into the picture
    canvas = canvas.convert("RGBa")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    digits = len(str(args.frames - 1))
    encode = encode_indexed4 if args.format == "indexed4" else encode_true_color_alpha
    frames = []
    total = 0
    for i in range(args.frames):
        angle = i * 360 / args.frames
        frame = canvas.rotate(-angle, resample=Image.Resampling.BICUBIC).convert("RGBA")
        data = encode(frame)
        (outdir / f"{args.name}{i:0{digits}d}.bin").write_bytes(data)
        frames.append(frame)
        total += len(data)

    if args.preview:
        columns = math.ceil(math.sqrt(args.frames))
        rows = math.ceil(args.frames / columns)
        sheet = Image.new("RGBA", (columns * size, rows * size), (40, 40, 40, 255))
        for i, frame in enumerate(frames):
            sheet.alpha_composite(frame, ((i % columns) * size, (i // columns) * size))
        sheet.save(args.preview)

    face = outdir.name
    print(f"wrote {args.frames} frames of {size}x{size} px, {total / 1024:.1f} KB total")
    print(f"use: image=/canvas/{face}/{args.name}{{frame:0{digits}}}.bin frames={args.frames}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
