#!/usr/bin/env python3
"""Render an annotated socket-placement study from the SAVED native PCB.

Run with KiCad's pcbnew Python. This does not modify the PCB. Rendering checks
outline size, footprints, pad geometry and socket net assignments against the
saved schematic netlist. It does not qualify the footprint or complete layout.
"""
import html
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware/top-board"


def main():
    board = pcb.LoadBoard(str(PROJECT / "NumitronTop.kicad_pcb"))
    config = json.loads((PROJECT / "socket-footprint.json").read_text())
    roles = {"V1": "H10", "V2": "H1", "V3": "M10", "V4": "M1"}
    footprints = {f.GetReference(): f for f in board.GetFootprints()}
    assert set(footprints) == set(roles), "Renderer is for the socket-only study; update it for further placement."
    assert len(list(board.GetTracks())) == 0
    edges = [d for d in board.GetDrawings() if d.GetLayer() == pcb.Edge_Cuts]
    assert len(edges) == 4
    corners = [(pcb.ToMM(p.x), pcb.ToMM(p.y)) for e in edges for p in [e.GetStart(), e.GetEnd()]]
    ox, oy = min(x for x, y in corners), min(y for x, y in corners)
    width, height = max(x for x, y in corners) - ox, max(y for x, y in corners) - oy
    assert (width, height) == (110, 30)
    netlist = ET.parse(ROOT / "review/NumitronTop.net.xml").getroot()
    expected = {(n.get("ref"), n.get("pin")): net.get("name")
                for net in netlist.findall("nets/net") for n in net.findall("node")}
    all_refs = {c.get("ref") for c in netlist.findall("components/comp")}
    centers, count = [], 0
    min_edge_clearance = 100
    for ref, f in sorted(footprints.items()):
        x, y = pcb.ToMM(f.GetPosition().x) - ox, pcb.ToMM(f.GetPosition().y) - oy
        centers.append((x, y))
        assert f.GetLayer() == pcb.F_Cu and f.GetOrientationDegrees() == 0
        assert f.GetFPID().GetLibItemName() == config["name"]
        assert {p.GetNumber() for p in f.Pads()} == {str(n) for n in range(1, 10)}
        for p in f.Pads():
            assert p.GetNetname() == expected[(ref, p.GetNumber())]
            assert pcb.ToMM(p.GetDrillSize().x) == config["plated_hole_diameter_mm"]
            assert pcb.ToMM(p.GetSize().x) == config["copper_pad_size_mm"]
            px, py = pcb.ToMM(p.GetPosition().x) - ox, pcb.ToMM(p.GetPosition().y) - oy
            min_edge_clearance = min(min_edge_clearance, px - 1.9, width - px - 1.9, py - 1.9, height - py - 1.9)
            count += 1
        assert min(x, width-x, y, height-y) >= config["courtyard_radius_mm"]
    pitches = [math.dist(a, b) for a, b in zip(centers, centers[1:])]
    assert min(pitches) >= 2 * config["courtyard_radius_mm"]
    missing = sorted(all_refs - set(footprints))
    report = [
        "SOCKET PLACEMENT STUDY - NOT COMPLETE PCB LAYOUT",
        f"Board outline: {width:g} x {height:g} mm; two copper layers.",
        f"Saved native footprints: {len(footprints)}; {count} pads match schematic nets.",
        f"Socket centers relative to upper-left board corner (mm): {centers}",
        f"Center pitches (mm): {pitches}",
        f"Minimum separation between circular socket courtyards: {min(pitches)-24:g} mm.",
        f"Minimum socket-pad copper to board edge: {min_edge_clearance:.3f} mm.",
        f"Minimum glass-envelope separation: {min(pitches)-config['tube_glass_diameter_max_mm']:.2f} mm.",
        f"Unplaced schematic components ({len(missing)}): {', '.join(missing)}",
        "No tracks, vias, copper pours or mounting holes. Underside fit has not been established.",
        "Socket physical fit, terminal thickness and pin numbering remain provisional.",
    ]
    (ROOT / "review/placement-checks.txt").write_text("\n".join(report) + "\n")

    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="750" viewBox="0 0 1500 750">',
             '<rect width="1500" height="750" fill="#f3f5f1"/>',
             '<style>text{font-family:Arial,Helvetica,sans-serif} .dim{fill:#50655d;font-size:20px} .note{fill:#50655d;font-size:20px}</style>']

    def text(x, y, value, size=20, color="#193e33", anchor="start", weight="400"):
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{html.escape(value)}</text>')

    def line(x1, y1, x2, y2, color="#82968c", thickness=1.5, dash=""):
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{thickness}" stroke-dasharray="{dash}"/>')

    def circle(x, y, r, stroke, fill="none", thickness=1.5, dash=""):
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" stroke="{stroke}" fill="{fill}" stroke-width="{thickness}" stroke-dasharray="{dash}"/>')

    def hdim(x1, x2, y, label):
        line(x1, y, x2, y)
        line(x1, y-7, x1, y+7)
        line(x2, y-7, x2, y+7)
        text((x1+x2)/2, y-10, label, 20, "#50655d", "middle")

    text(90, 63, "NUMITRON / TOP BOARD", 32, weight="700")
    text(90, 102, "Socket placement study · top view", 24)
    parts.append('<rect x="1090" y="40" width="320" height="40" rx="20" fill="#e7cd90"/>')
    text(1250, 67, "DRAFT · UNROUTED", 19, "#5b4317", "middle", "700")
    text(1410, 104, "26 SEP 2026", 17, "#50655d", "end")
    scale, bx, by = 11, 145, 220
    hdim(bx, bx + width*scale, 175, "110 mm")
    line(bx, 185, bx, by-9)
    line(bx+width*scale, 185, bx+width*scale, by-9)
    line(103, by, 103, by+height*scale)
    line(96, by, 110, by)
    line(96, by+height*scale, 110, by+height*scale)
    parts.append(f'<text x="83" y="{by+height*scale/2}" text-anchor="middle" transform="rotate(-90 83 {by+height*scale/2})" class="dim">30 mm</text>')
    parts.append(f'<rect x="{bx}" y="{by}" width="{width*scale}" height="{height*scale}" fill="#16483d" stroke="#10372e" stroke-width="2"/>')
    text(bx+15, by+27, "REAR", 13, "#c9dcd2")
    text(bx+15, by+height*scale-15, "FRONT", 13, "#c9dcd2")
    for ref, fp in sorted(footprints.items()):
        cx = bx + (pcb.ToMM(fp.GetPosition().x)-ox)*scale
        cy = by + (pcb.ToMM(fp.GetPosition().y)-oy)*scale
        circle(cx, cy, config["tube_glass_diameter_max_mm"]/2*scale, "#a8d2c3", thickness=1.7, dash="6 5")
        circle(cx, cy, config["body_diameter_mm"]/2*scale, "#e6ede2", "#25574a", 2.0)
        for pad in fp.Pads():
            px = bx + (pcb.ToMM(pad.GetPosition().x)-ox)*scale
            py = by + (pcb.ToMM(pad.GetPosition().y)-oy)*scale
            radius = pcb.ToMM(pad.GetSize().x)/2*scale
            if pad.GetShape() == pcb.PAD_SHAPE_RECT:
                parts.append(f'<rect x="{px-radius}" y="{py-radius}" width="{2*radius}" height="{2*radius}" fill="#dfbd67"/>')
            else:
                circle(px, py, radius, "#dfbd67", "#dfbd67", 0)
            circle(px, py, pcb.ToMM(pad.GetDrillSize().x)/2*scale, "#0f362b", "#f3f5f1", 1)
            if pad.GetNumber() == "1":
                text(px-25, py-24, "1", 17, "#e6ede2", "middle")
        text(cx, cy-3, roles[ref], 29, "#ffffff", "middle", "700")
        text(cx, cy+29, ref, 19, "#cee3d7", "middle")
    for i, pitch in enumerate(pitches):
        hdim(bx+centers[i][0]*scale, bx+centers[i+1][0]*scale, 605, f"{pitch:g} mm centres")
    circle(159, 654, 7, "#dfbd67", "#dfbd67", 0)
    text(176, 662, "Provisional pads / holes", 18)
    line(475, 654, 511, 654, "#548d78", 2, "6 5")
    text(523, 662, "Maximum tube-glass envelope", 18)
    circle(930, 654, 9, "#25574a", thickness=2)
    text(950, 662, "18 mm socket body", 18)
    text(145, 710, "V1–V4 placed. Driver, connector, sensor, power and mounting placement remain to be completed.", 20)
    parts.append('</svg>')
    (ROOT / "review/NumitronTop-placement.svg").write_text("\n".join(parts) + "\n")
    print("\n".join(report))


if __name__ == "__main__":
    main()
