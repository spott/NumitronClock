# Numitron Clock

Top-board schematic and PCB layout for the four-tube clock described in the Obsidian note `electronics/Numitron Clock/Numitron Clock.md`, read on 2026-09-18. The detailed top-board decisions in that note supersede its older, general power and interconnect descriptions.

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
- [Top layout](review/NumitronTop-top.png), [underside layout](review/NumitronTop-bottom.png) and [dimensions / review notes](docs/placement.md)
- [Bring-up and ordering checks](docs/bring-up.md)
- [Archived component datasheets](datasheets/README.md)
- [ERC result](review/erc.rpt) and [exported-netlist audit](review/connectivity.txt)

The top board is placed and routed on a **110 × 40 mm working outline** with all 55 schematic parts, four M2.5 mounting positions, local power distribution and ground copper on both faces. The extra depth provides a separate underside strip for the wide SOIC drivers. The [layout notes](docs/placement.md) explain component placement, the perpendicular underside connector orientation and review process.

The GZC9-A socket footprint remains **provisional**, as explicitly authorized on 2026-09-25: 18 mm assumed tail circle, 0.5 mm estimated terminal thickness, 2.5 mm plated holes and 3.8 mm copper lands. Verify physical fit before ordering. Enclosure/cable fit, exact capacitor order codes and hardware measurements also remain assembly/release checks. **WWVB versus GPS belongs to the bottom board.**

The owner confirms the actual tubes are **marked DR2000 and have prefix decimal points**. The archived RCA table assigns that feature to DR2010 instead. The design preserves the requested HH.MM display and routes the eighth channel to pin 1; verify that decimal connection on the actual tubes before enabling it.

## Development

Use the pinned Nix flake; no global package installation is required. KiCad is supplied by the existing local application installation on macOS. The flake pins the supporting Python, Poppler, SVG-rendering and local Freerouting tools, not that external KiCad application.

```sh
nix develop
bash scripts/review.sh
```

The review command runs KiCad ERC, audits the saved schematic's netlist and provisional socket footprint, exports schematic and footprint SVGs, and renders inspection PNGs under ignored `tmp/render/`. It does not regenerate or overwrite the schematic or footprint. Source PDFs and the socket drawing are archived in Git with their provenance and hashes.

`scripts/build_schematic.py --write` records the initial schematic capture and is deliberately opt-in: it **overwrites the native KiCad files**. After editing in KiCad, preserve those edits; reconcile the generator before using it again.

`hardware/top-board/socket-footprint.json` records the socket assumptions. `scripts/build_socket_footprint.py --write` captures them into the project-local `Numitron.pretty` library; reconcile manual footprint edits before regenerating. The schematic assigns `Numitron:GZC9-A_B9A_Provisional` to V1-V4.

`nix develop --command bash scripts/review_placement.sh` checks the saved PCB against the netlist, runs DRC with schematic parity and generates the top/bottom review drawings. It does not regenerate placement or routing. [board-drc.json](review/board-drc.json) and [placement-checks.txt](review/placement-checks.txt) retain the results.

`build_placement.py --write` is a one-time placement capture using KiCad's bundled Python; it refuses to discard routing without an explicit override. `placement.json` is the initial coordinate record, while the saved native board is authoritative. The power routing, local-router exchange and ground-fill helpers likewise require care around later CAD edits; do not run capture scripts just to review the design.

The repository covers the future whole clock, but this revision contains only the top board. The bottom board will supply protected 5 V, regulated 3.3 V, the control interface and I2C pull-ups. Its MCU, USB-C input, RTC, time receiver, user controls and power telemetry are outside this milestone.
