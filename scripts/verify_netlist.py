#!/usr/bin/env python3
"""Audit KiCad's exported connectivity against the component pin tables.

Does not import the schematic generator: these assertions operate on KiCad's
interpretation of the actual saved schematic, including its hierarchy.
"""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
tree = ET.parse(ROOT / "review/NumitronTop.net.xml").getroot()
components = {c.attrib["ref"]: c for c in tree.find("components")}
nets = {}
members = {}
checks = 0
for net in tree.find("nets"):
    name = net.attrib["name"]
    members[name] = {(p.attrib["ref"], p.attrib["pin"]) for p in net.findall("node")}
    for node in members[name]:
        assert node not in nets, f"Pin in two nets: {node}"
        nets[node] = name

def require(ref, pin, expected):
    global checks
    actual=nets.get((ref,str(pin)))
    assert actual == expected, f"{ref}.{pin}: {actual!r}, expected {expected!r}"
    checks+=1

def joined(*pins):
    global checks
    names={nets.get((ref,str(pin))) for ref,pin in pins}
    assert len(names)==1 and None not in names, f"Not joined: {pins}: {names}"
    checks+=1

def value(ref, expected):
    global checks
    actual=components[ref].findtext("value")
    assert actual == expected, f"{ref}: {actual!r}, expected {expected!r}"
    checks+=1

assert len(components)==55, f"Unexpected component count: {len(components)}"
assert len({nets[("TP1","1")],nets[("TP2","1")],nets[("TP3","1")],nets[("TP4","1")]})==4, "Power rails shorted"
for pin,name in {1:"GND",2:"SER_3V3",3:"GND",4:"SRCK_3V3",5:"GND",6:"RCK_3V3",7:"GND",8:"BLANK_3V3",9:"+3V3",10:"SDA",11:"GND",12:"SCL",13:"DISPLAY_ARM",14:"+5V",15:"GND",16:"+5V"}.items(): require("J1",pin,name)
for pin,name in {1:"+5V",2:"GND",4:"+5V",5:"V_TUBE"}.items(): require("U1",pin,name)
joined(("U1",3),("R1",2),("R2",1))
require("R1",1,"V_TUBE"); require("R2",2,"GND")
for pin,name in {2:"SER_3V3",5:"SRCK_3V3",9:"RCK_3V3",12:"BLANK_3V3",14:"+5V",7:"GND"}.items(): require("U2",pin,name)
joined(("U2",1),("U2",4),("U2",10),("U2",13),("Q1",3),("R15",2))
require("R15",1,"+5V"); require("Q1",2,"GND")
joined(("Q1",1),("R16",2))
require("R16",1,"DISPLAY_ARM"); require("R17",1,"DISPLAY_ARM"); require("R17",2,"GND")
for output,r,signal in [(3,"R3","SER_5V"),(6,"R4","SRCK_5V"),(8,"R5","RCK_5V"),(11,"R6","BLANK_5V")]:
    joined(("U2",output),(r,1)); require(r,2,signal)
require("R10",1,"+5V"); require("R10",2,"BLANK_5V")
require("R14",1,"+3V3"); require("R14",2,"BLANK_3V3")
for ref,signal in [("R7","SER_5V"),("R8","SRCK_5V"),("R9","RCK_5V")]:
    require(ref,1,signal); require(ref,2,"GND"); value(ref,"100k")
for ref,signal in [("R11","SER_3V3"),("R12","SRCK_3V3"),("R13","RCK_3V3")]:
    require(ref,1,signal); require(ref,2,"GND"); value(ref,"4.7k")
# Preserve the A2 E9 workaround and the sensor address leakage margin.
value("R17","4.7k"); value("R19","10k")
value("R15","1k"); value("R16","2.2k")
for ref in ["U5","U6","U7","U8"]:
    for pin,name in {2:"+5V",8:"+5V",9:"BLANK_5V",10:"GND",11:"GND",19:"GND",12:"RCK_5V",13:"SRCK_5V"}.items(): require(ref,pin,name)
    for pin in [1,20]:
        assert len(members[nets[(ref,str(pin))]])==1, f"NC pin wired: {ref}.{pin}"
require("U5",3,"SER_5V")
joined(("U5",18),("U6",3)); joined(("U6",18),("U7",3)); joined(("U7",18),("U8",3)); joined(("U8",18),("TP5",1))
# Physical RCA socket pins, independent of graphical segment labels.
for driver,tube in [("U5","V1"),("U6","V2"),("U7","V3"),("U8","V4")]:
    require(tube,2,"V_TUBE")
    for drain,base in [(4,7),(5,8),(6,5),(7,4),(14,3),(15,9),(16,6),(17,1)]:
        joined((driver,drain),(tube,base))
        assert len(members[nets[(tube,str(base))]])==2, f"Unexpected segment branch at {tube}.{base}"
for pin,name in {1:"+3V3",3:"GND",4:"SDA",6:"SCL"}.items(): require("U3",pin,name)
require("U4",1,"GND"); require("U4",3,"+3V3")
joined(("U4",2),("R18",1)); joined(("U3",5),("R18",2),("C6",1)); joined(("U3",2),("R19",1))
require("R19",2,"GND"); require("C6",2,"GND")
for r,signal in [("R20","SDA"),("R21","SCL")]:
    require(r,1,"+3V3"); require(r,2,signal)
    assert any(p.attrib.get("name")=="dnp" for p in components[r].findall("property")), f"{r} must be DNP"

# Ensure every actual part links to a committed document, not a stale web-only field.
for ref,part in components.items():
    ds=part.findtext("datasheet") or ""
    if ref.startswith("TP"): continue
    path=Path(ds.replace("${KIPRJMOD}",str(ROOT/"hardware/top-board")))
    assert path.is_file(), f"Missing datasheet for {ref}: {ds}"
    assert path.read_bytes().startswith(b"%PDF"), f"Not a PDF: {path}"
    checks+=1

text=f"PASS: {checks} connectivity/document assertions; {len(components)} components; {len(members)} nets.\n"
text+="Includes rail separation, all IDC pins, SRCK pin 13, all TPIC grounds, 32 filament paths, cascade order, blanking, DVI reset and DNP I2C pull-ups.\n"
text+="Not verified electrically on hardware. Socket pin-1 decimal connection and unassigned mechanical footprints remain release hold points.\n"
(ROOT/"review/connectivity.txt").write_text(text)
print(text,end="")
