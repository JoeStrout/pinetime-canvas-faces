"""Writes LVGL 7 binary images (.bin) as InfiniTime's Canvas face reads them."""
import struct

from PIL import Image

# LVGL 7 color formats (lv_img_cf_t)
CF_TRUE_COLOR_ALPHA = 5
CF_INDEXED_4BIT = 9
CF_INDEXED_8BIT = 10

FORMATS = ["indexed4", "indexed8", "truecolor"]


def header(cf: int, width: int, height: int) -> bytes:
    return struct.pack("<I", cf | (width << 10) | (height << 21))


def encode_true_color_alpha(img: Image.Image) -> bytes:
    """RGB565 with bytes swapped (LV_COLOR_16_SWAP), then 8-bit alpha: InfiniTime's ARGB8565_RBSWAP."""
    out = bytearray(header(CF_TRUE_COLOR_ALPHA, img.width, img.height))
    data = img.convert("RGBA").tobytes()
    for i in range(0, len(data), 4):
        r, g, b, a = data[i:i + 4]
        c16 = ((r * 31 + 127) // 255) << 11 | ((g * 63 + 127) // 255) << 5 | ((b * 31 + 127) // 255)
        out += bytes((c16 >> 8, c16 & 0xFF, a))
    return bytes(out)


def encode_indexed(img: Image.Image, bits: int) -> bytes:
    """Palette image with per-entry alpha: 4 bits (16 colors) or 8 bits (256 colors) per pixel."""
    colors = 1 << bits
    quantized = img.convert("RGBA").quantize(colors=colors, method=Image.Quantize.FASTOCTREE)
    palette = quantized.getpalette(rawmode="RGBA") or []
    palette = (palette + [0] * (colors * 4))[:colors * 4]
    cf = CF_INDEXED_4BIT if bits == 4 else CF_INDEXED_8BIT
    out = bytearray(header(cf, img.width, img.height))
    for i in range(colors):
        r, g, b, a = palette[i * 4:i * 4 + 4]
        out += bytes((b, g, r, a))  # lv_color32_t order
    pixels = quantized.tobytes()
    if bits == 8:
        out += pixels
    else:
        for y in range(img.height):
            row = list(pixels[y * img.width:(y + 1) * img.width])
            if len(row) % 2:
                row.append(0)
            out += bytes((row[i] << 4) | row[i + 1] for i in range(0, len(row), 2))
    return bytes(out)


def encode(img: Image.Image, fmt: str) -> bytes:
    if fmt == "indexed4":
        return encode_indexed(img, 4)
    if fmt == "indexed8":
        return encode_indexed(img, 8)
    return encode_true_color_alpha(img)
