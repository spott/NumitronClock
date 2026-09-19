#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p review tmp/render tmp/cache
export XDG_CACHE_HOME="$PWD/tmp/cache"
# Run native KiCad operations sequentially: concurrent CLI instances share a lock.
kicad-cli sch erc --severity-all --exit-code-violations -o review/erc.rpt hardware/top-board/NumitronTop.kicad_sch
kicad-cli sch export netlist --format kicadxml -o review/NumitronTop.net.xml hardware/top-board/NumitronTop.kicad_sch
python3 scripts/verify_netlist.py
python3 scripts/update_bom.py
kicad-cli sch export svg -o review/ hardware/top-board/NumitronTop.kicad_sch
for input in review/*.svg; do
  rsvg-convert -w 2600 "$input" -o "tmp/render/$(basename "${input%.svg}").png"
done
