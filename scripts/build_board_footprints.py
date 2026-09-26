#!/usr/bin/env python3
"""Capture datasheet-based top-board footprints. --write overwrites local CAD.

BH1750: bh1750fvi.pdf pp. 14,16,17; rohm-wsof6-package.pdf p.7.
AP7361C: AP7361C.pdf pp.2,18,20. Header: idc-header.pdf p.1.
These are editable library files; reconcile manual edits before regenerating.
"""
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "hardware/top-board/libraries/Numitron.pretty"


def text(kind, value, x, y, layer, size=0.8, hide=False):
    return (f'(fp_text {kind} {json.dumps(value)} (at {x} {y}) (layer "{layer}") '
            f'{"hide" if hide else ""} (effects (font (size {size} {size}) (thickness 0.12))))')


def line(x1, y1, x2, y2, layer="F.Fab", width=0.1):
    return (f'(fp_line (start {x1} {y1}) (end {x2} {y2}) '
            f'(stroke (width {width}) (type solid)) (layer "{layer}"))')


def rect(x1, y1, x2, y2, layer="F.Fab", width=0.1):
    return (f'(fp_rect (start {x1} {y1}) (end {x2} {y2}) '
            f'(stroke (width {width}) (type solid)) (fill none) (layer "{layer}"))')


def pad(n, x, y, w, h, drill=None):
    if drill is not None:
        return (f'(pad "{n}" thru_hole {"rect" if n==1 else "circle"} (at {x} {y}) '
                f'(size {w} {h}) (drill {drill}) (layers "*.Cu" "*.Mask"))')
    return (f'(pad "{n}" smd rect (at {x} {y}) (size {w} {h}) '
            '(layers "F.Cu" "F.Paste" "F.Mask"))')


def model(path, angle=0):
    return (f'(model "${{KICAD10_3DMODEL_DIR}}/{path}" '
            f'(offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 {angle})))')


def write(name, description, attr, items):
    items = [text("reference", "REF**", 0, -3.1, "F.SilkS"),
             text("value", name, 0, 3.1, "F.Fab", hide=True)] + items
    (LIB / (name + ".kicad_mod")).write_text(
        f'(footprint "{name}" (version 20241229) (generator "pcbnew") (layer "F.Cu")\n'
        f' (descr {json.dumps(description)}) (attr {attr})\n ' + "\n ".join(items) + "\n)\n")
    print(name)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--write", action="store_true", required=True)
    p.parse_args()
    LIB.mkdir(parents=True, exist_ok=True)
    items = [rect(-0.8, -1.3, 0.8, 1.3), rect(-1.1, -1.9, 1.1, 1.9, "F.CrtYd", 0.05),
             line(-0.8, 0.95, -0.45, 1.3), line(-1.0, 1.1, -1.0, 1.65, "F.SilkS", 0.12),
             text("user", "${REFERENCE}", 0, 0, "F.Fab", 0.5)]
    for n, x, y in [(1, -.5, 1.375), (2, 0, 1.375), (3, .5, 1.375),
                    (4, .5, -1.375), (5, 0, -1.375), (6, -.5, -1.375)]:
        items.append(pad(n, x, y, .25, .55))
    # The six lands match the older WSOF6I terminal pitch/span. The exposed
    # centre is deliberately absent from copper, paste and mask openings.
    items.append('''(zone (net 0) (net_name "") (layers "F.Cu")
      (name "BH1750 exposed centre - no copper or vias") (hatch edge 0.5)
      (connect_pads (clearance 0)) (min_thickness 0.25) (filled_areas_thickness no)
      (keepout (tracks not_allowed) (vias not_allowed) (pads not_allowed)
        (copperpour not_allowed) (footprints allowed))
      (polygon (pts (xy -0.9 -0.95) (xy 0.9 -0.95) (xy 0.9 0.95) (xy -0.9 0.95))))''')
    write("ROHM_WSOF6I_BH1750_NoCenterPad",
          "BH1750FVI WSOF6I; 0.25x0.55 lands at 0.5 pitch, inner row gap 2.2; ROHM mounting reference p7. No centre solder/pad; front copper keepout.", "smd", items)

    items = [rect(-2.3, -1.35, 2.3, 1.35), rect(-2.55, -2.5, 2.55, 2.5, "F.CrtYd", .05),
             line(-2.42, .9, -2.42, 1.5, "F.SilkS", .12),
             line(-2.42, 1.5, -1.95, 1.5, "F.SilkS", .12)]
    for n, x, y in [(1, -1.5, 1.65), (3, 1.5, 1.65), (4, 1.5, -1.65), (5, -1.5, -1.65)]:
        items.append(pad(n, x, y, .68, 1.2))
    # Diodes' stepped ground land: 1.93x3.05 body plus 0.76-wide stem.
    # The 0.02 mm overlap ensures an unambiguous common copper region.
    items += [pad(2, 0, -.475, 1.93, 3.05), pad(2, 0, 1.64, .76, 1.22),
              model("Package_TO_SOT_SMD.3dshapes/SOT-89-5.step", 90)]
    write("Diodes_SOT89-5_AP7361C", "AP7361C-Y5; Diodes DS37274 p20 recommended lands; pin 2 is the stepped GND tab", "smd", items)

    items = [rect(-3.23, -5.1, 5.77, 22.88),
             rect(-3.83, -5.71, 6.37, 23.49, "F.CrtYd", .05),
             rect(-3.35, -5.22, 5.89, 23.00, "F.SilkS", .12),
             rect(-3.23, 6.64, -1.93, 11.14),
             line(-3.35, 6.64, -1.81, 6.64, "F.SilkS", .12),
             line(-1.81, 6.64, -1.81, 11.14, "F.SilkS", .12),
             line(-1.81, 11.14, -3.35, 11.14, "F.SilkS", .12),
             text("user", "1", -1.5, 0, "F.SilkS", .9)]
    for n in range(1, 17):
        items.append(pad(n, 2.54*((n-1)%2), 2.54*((n-1)//2), 1.8, 1.8, 1.1))
    items.append(model("Connector_IDC.3dshapes/IDC-Header_2x08_P2.54mm_Vertical.step"))
    write("Wurth_61201621621_2x08_P2.54mm", "Wurth 61201621621; 27.98x9.0 body, 2.54 grid, 1.1 mm finished drills; manufacturer drawing p1", "through_hole", items)

    items=['(pad "" np_thru_hole circle (at 0 0) (size 2.7 2.7) (drill 2.7) (layers "*.Cu" "*.Mask"))']
    for layer in ("F.CrtYd","B.CrtYd"):
        items.append(f'(fp_circle (center 0 0) (end 2.95 0) (stroke (width 0.05) (type solid)) (fill none) (layer "{layer}"))')
    items.append('(fp_circle (center 0 0) (end 2.7 0) (stroke (width 0.1) (type solid)) (fill none) (layer "Dwgs.User"))')
    points=" ".join(f"(xy {2.75*math.cos(n*math.pi/24):.6f} {2.75*math.sin(n*math.pi/24):.6f})" for n in range(48))
    for layer in ("F.Cu","B.Cu"):
        items.append(f'''(zone (net 0) (net_name "") (layer "{layer}") (hatch edge 0.5)
          (connect_pads (clearance 0)) (min_thickness 0.25)
          (keepout (tracks not_allowed) (vias not_allowed) (pads allowed) (copperpour not_allowed) (footprints allowed))
          (fill (thermal_gap 0.3) (thermal_bridge_width 0.3)) (polygon (pts {points})))''')
    write("MountingHole_2.7mm_M2.5_BothSides", "2.7 mm nonplated M2.5 clearance; 5.9 mm screw-head reserve on both faces", "through_hole board_only exclude_from_pos_files exclude_from_bom", items)


if __name__ == "__main__":
    main()
