#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p review tmp/render tmp/cache
export XDG_CACHE_HOME="$PWD/tmp/cache"
kicad_python="${KICAD_PYTHON:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9}"
"$kicad_python" scripts/verify_board.py
kicad-cli pcb drc --schematic-parity --severity-all --exit-code-violations --format json \
  -o review/board-drc.json hardware/top-board/NumitronTop.kicad_pcb
for side in F B; do
  extra=()
  label=top
  if [ "$side" = B ]; then extra=(--mirror); label=bottom; fi
  kicad-cli pcb export svg --layers "${side}.Cu,${side}.SilkS,${side}.Fab,Edge.Cuts" \
    --mode-single --fit-page-to-board --exclude-drawing-sheet "${extra[@]}" \
    -o "review/NumitronTop-${label}-copper.svg" hardware/top-board/NumitronTop.kicad_pcb
  kicad-cli pcb export svg --layers "${side}.Cu,${side}.SilkS,${side}.Fab,Edge.Cuts" \
    --mode-single --fit-page-to-board --exclude-drawing-sheet "${extra[@]}" \
    -o "tmp/${label}-routing.svg" tmp/layout-view.kicad_pcb
done
python3 scripts/render_placement.py
for side in top bottom; do
  rsvg-convert -w 2400 "review/NumitronTop-${side}.svg" -o "review/NumitronTop-${side}.png"
done
