# Numitron Clock

V1 top-board schematic for the four-tube clock described in the Obsidian note `electronics/Numitron Clock/Numitron Clock.md`, read on 2026-09-18. The detailed top-board decisions in that note supersede its older, general power and interconnect descriptions.

Open **[NumitronTop.kicad_pro](hardware/top-board/NumitronTop.kicad_pro)** in KiCad. The design was captured and checked with **KiCad 10.0.5**. All schematic symbols are included in the project-local library and embedded in the sheets.

## Review this revision

- [Power and inter-board interface](review/NumitronTop.svg)
- [Control and light sensor](review/NumitronTop-Logic%20_%20ambient%20light.svg)
- [Four tube drivers](review/NumitronTop-Four%20tube%20drivers.svg)
- [Connector and firmware contract](docs/interface.md)
- [Electrical design notes](docs/design.md)
- [Preliminary BOM](docs/bom.md)
- [Socket drawing and dimensions](docs/socket.md)
- [Provisional socket footprint](review/GZC9-A_B9A_Provisional.svg)
- [Bring-up and layout hold points](docs/bring-up.md)
- [Archived component datasheets](datasheets/README.md)
- [ERC result](review/erc.rpt) and [exported-netlist audit](review/connectivity.txt)

The schematic is captured and the four tubes now have a **provisional socket footprint** for top-board placement/layout. On 2026-09-25 the owner authorized using the drawing and estimating terminal thickness: the working footprint uses an 18 mm pin circle, 0.5 mm assumed thickness, 2.5 mm plated holes and 3.8 mm copper pads. Physical fit is checked before ordering boards; it does not block placement. No routed PCB or Gerbers are included yet. BH1750 land-pattern work, mechanical placement and thermal design remain top-board work. **WWVB versus GPS belongs to the bottom board and does not block this board.**

The owner confirms the actual tubes are **marked DR2000 and have prefix decimal points**. The archived RCA table assigns that feature to DR2010 instead. The design preserves the requested HH.MM display and routes the eighth channel to pin 1; verify that decimal connection on the actual tubes before enabling it.

## Development

Use the pinned Nix flake; no global package installation is required. KiCad is supplied by the existing local application installation on macOS. The flake pins the supporting Python, Poppler and SVG-rendering tools, not that external KiCad application.

```sh
nix develop
bash scripts/review.sh
```

The review command runs KiCad ERC, audits the saved schematic's netlist and provisional socket footprint, exports schematic and footprint SVGs, and renders inspection PNGs under ignored `tmp/render/`. It does not regenerate or overwrite the schematic or footprint. Source PDFs and the socket drawing are archived in Git with their provenance and hashes.

`scripts/build_schematic.py --write` records the initial schematic capture and is deliberately opt-in: it **overwrites the native KiCad files**. After editing in KiCad, preserve those edits; reconcile the generator before using it again.

`hardware/top-board/socket-footprint.json` records the socket assumptions. `scripts/build_socket_footprint.py --write` captures them into the project-local `Numitron.pretty` library; reconcile manual footprint edits before regenerating. The schematic assigns `Numitron:GZC9-A_B9A_Provisional` to V1-V4.

The repository covers the future whole clock, but this revision contains only the top board. The bottom board will supply protected 5 V, regulated 3.3 V, the control interface and I2C pull-ups. Its MCU, USB-C input, RTC, time receiver, user controls and power telemetry are outside this milestone.
