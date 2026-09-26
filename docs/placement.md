# Top-board layout, revision 0.2

[Top view](../review/NumitronTop-top.png) · [Underside view](../review/NumitronTop-bottom.png) · [Editable PCB](../hardware/top-board/NumitronTop.kicad_pcb) · [DRC and schematic parity](../review/board-drc.json)

The native KiCad PCB contains all 55 schematic components, four mounting holes, routed connections and ground copper on both faces. The working outline is **110 × 40 mm**, two layers, 1.6 mm thick. The extra 10 mm of depth accommodates the wide SOIC drivers in a strip clear of the socket tails. The earlier 110 × 30 mm socket study is superseded. Enclosure acceptance of the working depth and cable access is still a physical integration check; no board order has been placed.

Coordinates are millimetres from the upper-left of the board in the top view: +X is right, +Y is toward the front. The native board corner is (50, 50) mm.

| Item | Face | X | Y | Notes |
|---|---|---:|---:|---|
| V1 / hour tens | Top | 14.5 | 13 | Provisional GZC9-A |
| V2 / hour units | Top | 39 | 13 | Provisional GZC9-A |
| V3 / minute tens | Top | 71 | 13 | Candidate prefix decimal separator |
| V4 / minute units | Top | 95.5 | 13 | Provisional GZC9-A |
| U5–U8 / drivers | Bottom | Same as corresponding tube | 31 | SOIC bodies below the socket-tail region |
| J1 / header body centre | Bottom | 55 | 14.9 | Long axis front to rear; key toward +X in top view |
| U1 / regulator | Bottom | 26.75 | 4 | Ground tab and six nearby thermal vias |
| U2 / level shifter | Bottom | 39 | 13 | Inside V2 tail ring |
| U3 / light sensor | Top | 55 | 2.7 | Rear, between the digit pairs |
| C10 / U6 bypass | Top | 34.5 | 31.5 | Gives the capacitor a connected ground plane |
| H1, H2 | Both | 3, 107 | 3 | 2.7 mm NPTH, proposed M2.5 hardware |
| H3, H4 | Both | 3, 107 | 37 | 2.7 mm NPTH, proposed M2.5 hardware |

Within each digit pair the pitch is 24.5 mm; between pairs it is 32 mm. RCA's 19.94 mm maximum glass diameter gives 4.56 mm and 12.06 mm glass-envelope gaps respectively. The provisional 24 mm socket courtyards have a 0.5 mm minimum separation. Driver bodies occupy a separate underside strip, not the projected socket-tail circle. Cable housing, strain relief, bend radius, actual tail length and enclosure clearances still need a physical fit check.

## Copper and assembly

The 5 V input and V_TUBE distribution use 1 mm trunks. The regulator has short 0.5 mm connections at its narrow lands, two vias at each main supply layer transition, local input/output capacitors, direct tab-to-ground copper and six 0.3 mm drilled thermal vias. Ground zones on both faces provide the return and heat-spreading copper. SMD grounds connect directly to their local pours; J1 uses soldering thermals except pin 7, which has a direct connection. C10 sits on the tube side above U6 so its return is not isolated by the surrounding routes. Mounting heads have 5.5 mm copper/track/via keepouts on both faces. Typical signals are 0.25 mm with 0.20 mm local necks. See the native board and saved DRC for actual geometry. Bench measurements, not copper area alone, establish regulator temperature and filament inrush behavior.

R20/R21 are DNP I2C pull-ups. Small component references are on the fabrication/assembly layers to avoid crowding solder lands; the board silk retains the tube roles, driver references, connector identification and test-point labels. Bottom review images are mirrored to show the face seen when the board is turned over.

The sensor has six lands and **no soldered centre pad**. Its front-side centre has a copper, track, via and pad keepout. The generic ROHM WSOF6 recommended land pattern was compared with the older BH1750 WSOF6I package drawing: 0.5 mm lead pitch, 2.2 mm inner land-row gap and 0.25 × 0.55 mm lands. The old pin-1 drawing has a 0.525 mm offset and a wider identification lead; this small difference and the optical package require inspection against actual parts before assembly release. Keep the exposed centre unsoldered. An optical shield may be needed if the tubes influence ambient readings.

U1 uses the AP7361C-specific stepped ground land from Diodes' recommended pattern, rather than the stock SOT89-5 tab. J1 uses Wurth's 1.1 mm recommended finished holes, 2.54 mm grid and 27.98 × 9 mm body outline. Package references and page numbers are recorded in the custom footprint generator; original documents are committed in `datasheets/`.

## Review and editing

Run `nix develop --command bash scripts/review.sh` for schematic/ERC/netlist checks, then `nix develop --command bash scripts/review_placement.sh` for the saved PCB's geometry audit, DRC, parity and images. The layout review requires no suppressed DRC findings and no unrouted connections. Automated checks do not establish physical socket fit, component procurement, solderability or measured thermal performance.

Native KiCad files remain authoritative. `placement.json` records the starting placements. `build_placement.py --write` refuses to discard tracks unless explicitly told to do so; even with that safeguard, reconcile CAD edits before regeneration. `route_board.py` records the initial power trunks and provides local SPECCTRA import/export and copper-fill helpers. Subsequent cleanup is preserved in the native PCB. Do not regenerate the board to review it.

The local Freerouting tool is pinned through the Nix flake and operates on local files. The supporting SVG/PDF/Python tools are also pinned; the installed KiCad 10.0.5 application supplies the CAD engine. No global packages or remote routing service are required.

The [provisional socket assumptions](socket.md) remain authorized for layout. Verify the socket fit, tube pin-1 decimal mapping and [bring-up hold points](bring-up.md) before ordering or powering the assembly. **WWVB versus GPS is bottom-board work.**
