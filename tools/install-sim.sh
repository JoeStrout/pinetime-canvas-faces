#!/bin/sh
# Copies faces into an InfiniSim flash image.
# Usage: tools/install-sim.sh [path/to/littlefs-do] [face ...]
# Run it from the directory holding spiNorFlash.raw, with the simulator closed.
set -e

here=$(cd "$(dirname "$0")/.." && pwd)
littlefs=${1:-littlefs-do}
[ $# -gt 0 ] && shift

if [ $# -eq 0 ]; then
  set -- $(ls "$here/faces")
fi

"$littlefs" mkdir /canvas >/dev/null 2>&1 || true
for face in "$@"; do
  dir="$here/faces/$face"
  "$littlefs" cp "$dir/$face.cfg" /canvas
  assets=$(find "$dir" -type f ! -name "$face.cfg")
  if [ -n "$assets" ]; then
    "$littlefs" mkdir "/canvas/$face" >/dev/null 2>&1 || true
    "$littlefs" cp $assets "/canvas/$face"
  fi
  echo "installed $face"
done
