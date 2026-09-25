#!/usr/bin/env python3
"""Structural checks for Canvas faces.

This does not re-implement the firmware's parser; it catches the mistakes that
are easy to make in a pull request: bad layout, missing assets, lines or names
too long for the watch, and a missing `requires` line.

Usage: tools/check.py [faces_dir]
"""
import re
import sys
from pathlib import Path

# Must match the firmware (src/displayapp/screens/WatchFaceCanvas.h)
FORMAT_VERSION = 1
MAX_LINE = 127
MAX_FILE_NAME = 31
MAX_ELEMENTS = 48
MAX_LOADED_FONTS = 4

ELEMENTS = {"text", "image", "rect", "line", "arc", "hand", "ticks", "battery", "bar"}
DIRECTIVES = {"requires", "name", "bg"}

# Files installed by the standard InfiniTime resources package
STANDARD_RESOURCES = {
    "/fonts/teko.bin",
    "/fonts/bebas.bin",
    "/fonts/lv_font_dots_40.bin",
    "/fonts/7segments_40.bin",
    "/fonts/7segments_115.bin",
    "/images/pine_small.bin",
    "/images/navigation0.bin",
    "/images/navigation1.bin",
}


def check_face(face_dir: Path) -> list[str]:
    name = face_dir.name
    cfg = face_dir / f"{name}.cfg"
    errors = []

    def err(msg, line=None):
        where = f"{cfg}:{line}" if line else str(cfg)
        errors.append(f"{where}: {msg}")

    if not cfg.is_file():
        err("missing; each face folder needs <folder>.cfg")
        return errors
    if len(cfg.name) > MAX_FILE_NAME:
        err(f"file name longer than {MAX_FILE_NAME} characters")

    raw = cfg.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        err("not valid UTF-8")
        return errors

    elements = 0
    fonts = set()
    seen_requires = False
    for number, line in enumerate(text.splitlines(), start=1):
        if len(line.encode("utf-8")) > MAX_LINE:
            err(f"line longer than {MAX_LINE} bytes", number)
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        command = stripped.split()[0]
        if not seen_requires:
            if command != "requires":
                err("first line must be 'requires <version>'", number)
            seen_requires = True
        if command == "requires":
            parts = stripped.split()
            if len(parts) != 2 or not parts[1].isdigit():
                err("bad requires line", number)
            elif int(parts[1]) > FORMAT_VERSION:
                err(f"requires {parts[1]}, but this checker knows version {FORMAT_VERSION}", number)
            continue
        if command in DIRECTIVES:
            continue
        if command not in ELEMENTS:
            err(f"unknown element '{command}'", number)
            continue
        elements += 1

        paths = re.findall(r'font=(/\S+)', stripped)
        fonts.update(paths)
        if command == "image":
            tokens = stripped.split()
            if len(tokens) >= 4:
                paths.append(tokens[3])
        for path in paths:
            check_asset(path, name, face_dir, lambda msg: err(msg, number))

    if not seen_requires:
        err("missing 'requires <version>' line")
    if elements > MAX_ELEMENTS:
        err(f"{elements} elements; the watch allows {MAX_ELEMENTS}")
    if len(fonts) > MAX_LOADED_FONTS:
        err(f"{len(fonts)} font files; the watch loads at most {MAX_LOADED_FONTS}")
    return errors


def check_asset(path: str, name: str, face_dir: Path, err) -> None:
    if path in STANDARD_RESOURCES:
        return
    prefix = f"/canvas/{name}/"
    if not path.startswith(prefix):
        err(f"{path}: assets must live under {prefix} (or be a standard resource)")
        return
    if not (face_dir / path[len(prefix):]).is_file():
        err(f"{path}: file not found in {face_dir}")


def main() -> int:
    faces_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "faces")
    errors = []
    faces = sorted(d for d in faces_dir.iterdir() if d.is_dir())
    for face_dir in faces:
        errors += check_face(face_dir)
    for e in errors:
        print(e)
    print(f"{len(faces)} faces checked, {len(errors)} problems")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
