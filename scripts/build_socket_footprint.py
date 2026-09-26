#!/usr/bin/env python3
"""Capture the provisional GZC9-A footprint from editable mechanical assumptions.

Requires --write because the generated .kicad_mod is editable in KiCad. Reconcile
any manual footprint edits before regenerating. No third-party dependencies.
"""
from pathlib import Path
import argparse
import json
import math
import uuid

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware/top-board"
NS = uuid.UUID("eca1c72e-0595-45a3-a379-26743d8c086d")

def uid(key): return str(uuid.uuid5(NS,key))
def q(value): return json.dumps(str(value))
def point(radius,degrees):
    a=math.radians(degrees)
    return round(radius*math.cos(a),6),round(radius*math.sin(a),6)
def xy(p): return f"{p[0]:.6f} {p[1]:.6f}"

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write",action="store_true",required=True)
    parser.parse_args()
    c=json.loads((PROJECT/"socket-footprint.json").read_text())
    name=c["name"]
    directory=PROJECT/"libraries"/(c["library"]+".pretty")
    directory.mkdir(parents=True,exist_ok=True)
    pins=[(i,point(c["assumed_pad_circle_diameter_mm"]/2,
                  c["pin_1_angle_degrees_xy_down"]-(i-1)*c["assumed_pin_step_degrees"]))
          for i in range(1,c["pin_count"]+1)]
    items=[]
    def text(kind,value,pos,layer,size=1.0,hide=False):
        items.append(f'(fp_text {kind} {q(value)} (at {xy(pos)}) (layer "{layer}") '
                     f'{"hide" if hide else ""} (effects (font (size {size} {size}) (thickness 0.15))))')
    def circle(radius,layer,width=0.1):
        items.append(f'(fp_circle (center 0 0) (end {radius} 0) '
                     f'(stroke (width {width}) (type solid)) (fill none) (layer "{layer}"))')
    # Dimensions in fab/drawing layers are physical outlines, not more holes.
    circle(c["body_diameter_mm"]/2,"F.Fab")
    circle(c["tube_glass_diameter_max_mm"]/2,"Dwgs.User")
    circle(c["contact_circle_diameter_mm"]/2,"Dwgs.User",0.05)
    circle(c["courtyard_radius_mm"],"F.CrtYd",0.05)
    text("reference","REF**",(0,-13.3),"F.SilkS")
    text("value",name,(0,13.3),"F.Fab",hide=True)
    text("user","${REFERENCE}",(0,-1),"F.Fab")
    text("user","PROVISIONAL",(0,1),"F.Fab",0.8)
    # Pin-1 arrow inside the open indexing sector; it does not cross pad copper.
    for a,b in [((2.0,7.8),(2.0,6.8)),((2.0,6.8),(2.9,7.3)),((2.9,7.3),(2.0,7.8))]:
        items.append(f'(fp_line (start {xy(a)}) (end {xy(b)}) '
                     '(stroke (width 0.15) (type solid)) (layer "F.SilkS"))')
    # Draw only body-arc segments that clear every solder-mask opening.
    silk_radius=c["body_diameter_max_mm"]/2
    pad_half=c["copper_pad_size_mm"]/2
    clearance=0.35
    def clear(degrees):
        x,y=point(silk_radius,degrees)
        for number,(px,py) in pins:
            if number==1:
                distance=math.hypot(max(abs(x-px)-pad_half,0),max(abs(y-py)-pad_half,0))
                if distance<clearance:return False
            elif math.hypot(x-px,y-py)<pad_half+clearance:return False
        return True
    for degree in range(360):
        if all(clear(degree+fraction) for fraction in (0,0.5,1)):
            items.append(f'(fp_line (start {xy(point(silk_radius,degree))}) '
                         f'(end {xy(point(silk_radius,degree+1))}) '
                         '(stroke (width 0.12) (type solid)) (layer "F.SilkS"))')
    for number,pos in pins:
        shape="rect" if number==1 else "circle"
        items.append(f'(pad "{number}" thru_hole {shape} (at {xy(pos)}) '
                     f'(size {c["copper_pad_size_mm"]} {c["copper_pad_size_mm"]}) '
                     f'(drill {c["plated_hole_diameter_mm"]}) (layers "*.Cu" "*.Mask") '
                     f'(uuid "{uid(name+":"+str(number))}"))')
        # Internal fab labels remain readable in the native footprint preview.
        x,y=pos
        text("user",str(number),(x*0.72,y*0.72),"F.Fab",0.65)
    description=(f'{c["status"]}; assumed {c["assumed_pad_circle_diameter_mm"]} mm terminal PCD, '
                 f'{c["assumed_terminal_thickness_mm"]} mm terminal thickness, '
                 f'{c["plated_hole_diameter_mm"]} mm round PTH. '
                 'See docs/socket.md and hardware/top-board/socket-footprint.json.')
    content=(f'(footprint {q(name)} (version 20241229) (generator "pcbnew") (layer "F.Cu")\n'
             f'  (descr {q(description)}) (tags "GZC9-A B9A Noval provisional") (attr through_hole)\n'
             +'\n'.join('  '+item for item in items)+'\n)\n')
    target=directory/(name+".kicad_mod")
    target.write_text(content)
    (PROJECT/"fp-lib-table").write_text(
        '(fp_lib_table (version 7)\n'
        '  (lib (name "Numitron") (type "KiCad") (uri "${KIPRJMOD}/libraries/Numitron.pretty") '
        '(options "") (descr "Project footprints; socket dimensions provisional"))\n)\n')
    print(f"Wrote {target.relative_to(ROOT)}: 9 pads; provisional 18 mm PCD / 2.5 mm holes.")

if __name__=="__main__":main()
