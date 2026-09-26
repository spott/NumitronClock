#!/usr/bin/env python3
"""Check saved footprint geometry, separately from the capture script.

This validates the CAD implementation of documented assumptions, not physical fit.
"""
from itertools import combinations
from pathlib import Path
import json
import math
import sexpdata
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/"hardware/top-board"
c=json.loads((PROJECT/"socket-footprint.json").read_text())
path=PROJECT/"libraries"/(c["library"]+".pretty")/(c["name"]+".kicad_mod")
fp=sexpdata.loads(path.read_text())
def elements(node,tag):
    return [x for x in node if isinstance(x,list) and x and str(x[0])==tag]
def element(node,tag):
    found=elements(node,tag)
    assert len(found)==1,(tag,found)
    return found[0]

pads={p[1]:p for p in elements(fp,"pad")}
assert len(elements(fp,"pad"))==9 and set(pads)==set(map(str,range(1,10)))
centres={number:tuple(element(p,"at")[1:3]) for number,p in pads.items()}
radius=c["assumed_pad_circle_diameter_mm"]/2
for number,p in pads.items():
    assert str(p[2])=="thru_hole"
    assert str(p[3])==("rect" if number=="1" else "circle")
    assert element(p,"size")[1:]==[c["copper_pad_size_mm"]]*2
    assert element(p,"drill")[1:]==[c["plated_hole_diameter_mm"]]
    assert element(p,"layers")[1:]==["*.Cu","*.Mask"]
    assert abs(math.hypot(*centres[number])-radius)<1e-6
assert centres["1"][0]>0 and centres["1"][1]>0
assert abs(centres["5"][0])<1e-6 and centres["5"][1]<0
assert centres["9"][0]<0 and centres["9"][1]>0
angles={n:math.degrees(math.atan2(y,x))%360 for n,(x,y) in centres.items()}
assert all(abs((angles[str(n)]-angles[str(n+1)])%360-36)<1e-5 for n in range(1,9))
assert abs((angles["9"]-angles["1"])%360-72)<1e-5

half=c["copper_pad_size_mm"]/2
clearances=[]
for (a,pa),(b,pb) in combinations(pads.items(),2):
    xa,ya=centres[a]; xb,yb=centres[b]
    dx,dy=abs(xa-xb),abs(ya-yb)
    distance=(math.hypot(max(dx-half,0),max(dy-half,0))-half
              if "1" in (a,b) else math.hypot(dx,dy)-2*half)
    clearances.append(distance)
assert min(clearances)>=0.25,"Copper pads overlap or violate 0.25 mm clearance"
courtyard=next(x for x in elements(fp,"fp_circle") if element(x,"layer")[1]=="F.CrtYd")
assert element(courtyard,"center")[1:]==[0,0]
cr=math.hypot(*element(courtyard,"end")[1:])
extent=max(math.hypot(abs(x)+half,abs(y)+half) if n=="1" else math.hypot(x,y)+half
           for n,(x,y) in centres.items())
assert cr-extent>=0.25,"Courtyard does not enclose pad copper with clearance"
diagonal=math.hypot(c["terminal_width_mm"]+c["terminal_width_tolerance_mm"],
                    c["assumed_terminal_thickness_mm"])
assert c["plated_hole_diameter_mm"]-diagonal>=0.2
annulus=(c["copper_pad_size_mm"]-c["plated_hole_diameter_mm"])/2
assert annulus>=0.5

netlist=ET.parse(ROOT/"review/NumitronTop.net.xml").getroot()
parts={part.attrib["ref"]:part for part in netlist.find("components")}
for ref in ("V1","V2","V3","V4"):
    assert parts[ref].findtext("footprint")==c["library"]+":"+c["name"]

report=("PASS: saved provisional socket footprint matches the documented assumptions.\n"
        "9 unique numbered through-hole pads; top-view numbering and 36/72 degree pattern checked.\n"
        f'Pad circle {2*radius:.2f} mm; round holes {c["plated_hole_diameter_mm"]:.2f} mm; '
        f'copper pads {2*half:.2f} mm; nominal annular ring {annulus:.2f} mm.\n'
        f'Minimum copper clearance {min(clearances):.3f} mm; minimum courtyard margin {cr-extent:.3f} mm.\n'
        f'Assumed terminal diagonal {diagonal:.3f} mm; nominal diametral hole clearance '
        f'{c["plated_hole_diameter_mm"]-diagonal:.3f} mm.\n'
        "Assigned to V1-V4 in the native schematic netlist. Physical fit remains unverified.\n")
(ROOT/"review/socket-footprint-checks.txt").write_text(report)
print(report,end="")
