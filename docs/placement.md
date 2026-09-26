# Top-board socket placement study

[Placement image](../review/NumitronTop-placement.png) · [Native KiCad layer plot](../review/NumitronTop-placement-cad.svg) · [Editable PCB](../hardware/top-board/NumitronTop.kicad_pcb)

This is the first **socket-only placement study**, created 2026-09-26 to show the proposed tube arrangement. It is not a complete component placement. The saved PCB contains V1–V4 with their 36 pads assigned to the schematic nets, a 110 × 30 mm rectangular outline, and no routing. The other 51 schematic components and mounting holes have not been placed. Underside fit, connector access, sensor view, thermal copper and trace routing still need to be resolved.

Coordinates below are millimetres from the upper-left of the board in the top view; +X is right, +Y is toward the front. The native CAD origin for the board's upper-left corner is (50, 50) mm.

| Reference | Digit | X | Y |
|---|---|---:|---:|
| V1 | Hour tens | 17 | 15 |
| V2 | Hour units | 41.5 | 15 |
| V3 | Minute tens / prefix separator | 68.5 | 15 |
| V4 | Minute units | 93 | 15 |

Socket centres are 24.5 mm apart within each pair, and 27 mm apart between the pairs. With the archived RCA maximum glass diameter of 19.94 mm, the corresponding glass-envelope gaps are 4.56 mm and 7.06 mm. The provisional 24 mm circular socket courtyards have 0.5 mm minimum separation. These numbers describe the current drawing and assumptions, not a hardware fit test.

The annotated image is generated from the saved native board's footprint and pad positions. Solid circles show the nominal 18 mm socket bodies; dashed circles show the maximum glass envelope. Gold shapes and holes use the native pad sizes. It is a dimensional plan view, not a photograph or a 3D model of the sockets. Pin 1 is square, and the socket gaps face the front of the board.

The [socket assumptions](socket.md), including the estimated 0.5 mm terminal thickness and 18 mm pad circle, remain provisional as authorized by the owner. Verify physical fit before ordering. The hour/minute spacing can still change as the electronics and mounting are placed.

## Review and reproduction

Run `nix develop --command bash scripts/review_placement.sh`. It loads the saved PCB using the existing KiCad Python module, checks the outline and socket pad assignments against the exported schematic netlist, and generates the annotated SVG/PNG and native KiCad layer plot. [placement-checks.txt](../review/placement-checks.txt) records the checks and explicitly lists the unplaced parts.

The full [KiCad DRC / schematic parity result](../review/placement-drc.json) is retained without exclusions. Missing footprints and unrouted connections are expected at this stage; a clean manufacturing DRC is not claimed. The limited placement checks do not establish that the complete circuitry fits this outline.

`scripts/build_placement.py --write` captures the initial positions from `hardware/top-board/placement.json`. It overwrites the native PCB; preserve and reconcile later CAD edits before regenerating. Use the Python bundled with the existing KiCad application to run it; no global Python packages are required.

A [ROHM WSOF6 mounting reference](../datasheets/rohm-wsof6-package.pdf) was archived during this work for the pending BH1750 footprint audit. Its correspondence to the older BH1750 WSOF6I package still needs checking; this study does not assign or qualify a sensor land pattern.
