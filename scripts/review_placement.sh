#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p review tmp/render tmp/cache
export XDG_CACHE_HOME="$PWD/tmp/cache"

# pcbnew comes from the existing KiCad application; supporting render tools
# come from nix develop. No package installation is performed here.
kicad_python="${KICAD_PYTHON:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9}"
"$kicad_python" scripts/render_placement.py
kicad-cli pcb export svg --layers F.Cu,F.SilkS,F.Fab,Dwgs.User,Edge.Cuts \
  --mode-single --fit-page-to-board --exclude-drawing-sheet \
  -o review/NumitronTop-placement-cad.svg hardware/top-board/NumitronTop.kicad_pcb
# The study is deliberately incomplete. Keep the full parity/DRC report,
# including missing components and unrouted nets; do not suppress violations.
kicad-cli pcb drc --schematic-parity --severity-all --format json \
  -o review/placement-drc.json hardware/top-board/NumitronTop.kicad_pcb
rsvg-convert -w 1800 review/NumitronTop-placement.svg -o review/NumitronTop-placement.png
rsvg-convert -w 2200 review/NumitronTop-placement-cad.svg -o tmp/render/NumitronTop-placement-cad.png
