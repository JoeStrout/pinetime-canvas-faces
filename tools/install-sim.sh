#!/bin/sh
# Copies faces into an InfiniSim flash image.
# Usage: tools/install-sim.sh [path/to/littlefs-do] [face ...]
# Run it from the directory holding spiNorFlash.raw, with the simulator closed.
# Set FACES to install from another folder, e.g. FACES=private.
set -e

here=$(cd "$(dirname "$0")/.." && pwd)
faces="$here/${FACES:-faces}"
littlefs=${1:-littlefs-do}
[ $# -gt 0 ] && shift

if [ $# -eq 0 ]; then
  set -- $(ls "$faces")
fi

"$littlefs" mkdir /canvas >/dev/null 2>&1 || true
for face in "$@"; do
  dir="$faces/$face"
  "$littlefs" cp "$dir/$face.cfg" /canvas
  # Only LVGL images and fonts go to the watch, not source pictures
  assets=$(find "$dir" -type f -name "*.bin")
  if [ -n "$assets" ]; then
    "$littlefs" mkdir "/canvas/$face" >/dev/null 2>&1 || true
    "$littlefs" cp $assets "/canvas/$face"
  fi
  echo "installed $face"
done
