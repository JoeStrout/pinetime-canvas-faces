#!/usr/bin/env python3
"""Regenerates the Willie face's .bin images from the source PNGs. Run from this folder."""
import subprocess
import sys
from pathlib import Path

from PIL import Image

tools = Path(__file__).resolve().parents[2] / "tools"
sys.path.insert(0, str(tools))
import lvimage

HAND_SCALE = 0.24  # pointing hand: 174 px long in the source -> ~42 px
BODY_HEIGHT = 190

# Background glow: the display is RGB565, so a gray has only 32 levels. Dither to exactly
# those levels, or the gradient shows as rings.
bg = Image.open("BackgroundGlow.png").convert("L").resize((240, 240), Image.Resampling.LANCZOS)
grays = Image.new("P", (1, 1))
grays.putpalette([round(k * 255 / 31) for k in range(32) for _ in range(3)])
bg = bg.convert("RGB").quantize(palette=grays, dither=Image.Dither.FLOYDSTEINBERG).convert("RGBA")
Path("glow.bin").write_bytes(lvimage.encode(bg, "indexed8"))

# Body, facing left (as drawn) and mirrored to face right
body = Image.open("WillieBody.png").convert("RGBa")
w = round(body.width * BODY_HEIGHT / body.height)
body = body.resize((w, BODY_HEIGHT), Image.Resampling.LANCZOS).convert("RGBA")
Path("body.bin").write_bytes(lvimage.encode(body, "indexed8"))
Path("body_r.bin").write_bytes(lvimage.encode(body.transpose(Image.Transpose.FLIP_LEFT_RIGHT), "indexed8"))
print(f"body {body.width}x{body.height}")

# Pointing hand: rotate so the finger points up, crop, scale; the cuff centre is the pivot
hand = Image.open("PointingHand.png").convert("RGBA")
cuff = (92, 145)
hand = hand.rotate(90, expand=False)  # counter-clockwise
cuff = (cuff[1], hand.width - 1 - cuff[0])
box = hand.getbbox()
hand = hand.crop(box)
cuff = (cuff[0] - box[0], cuff[1] - box[1])
size = (round(hand.width * HAND_SCALE), round(hand.height * HAND_SCALE))
hand = hand.convert("RGBa").resize(size, Image.Resampling.LANCZOS).convert("RGBA")
cuff = (cuff[0] * HAND_SCALE, cuff[1] * HAND_SCALE)
tmp = Path("hand-up.png")
hand.save(tmp)
subprocess.run([sys.executable, str(tools / "make-frames.py"), str(tmp), ".", "--name", "hand",
                "--center", f"{cuff[0]:.1f},{cuff[1]:.1f}", "--preview", "hand-sheet.png"], check=True)
tmp.unlink()
