#!/usr/bin/env python3
"""Capture full top-board placement from placement.json and the saved netlist.

Requires --write. Refuses to discard existing routing unless --discard-routing
is explicitly supplied. Native KiCad files remain the editable source of truth;
reconcile subsequent CAD edits into placement.json before regenerating.
Run using the Python bundled with the installed KiCad application.
"""
import argparse
import json
import re
import xml.etree.ElementTree as ET
import pcbnew as pcb
from pcb_common import ROOT, PROJECT, BOARD, vec, load_footprint, text, save


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", required=True)
    parser.add_argument("--discard-routing", action="store_true")
    args=parser.parse_args()
    if BOARD.exists() and not args.discard_routing:
        old=pcb.LoadBoard(str(BOARD))
        assert not list(old.GetTracks()), "PCB has routing. Reconcile CAD edits; --discard-routing is required to replace it."
    config=json.loads((PROJECT/"placement.json").read_text())
    netlist=ET.parse(ROOT/"review/NumitronTop.net.xml").getroot()
    components={c.get("ref"):c for c in netlist.findall("components/comp")}
    assert set(components)==set(config["parts"]), "Every schematic part must have a placement."
    root_uuid=re.search(r'\(uuid "?([0-9a-f-]+)"?\)',(PROJECT/"NumitronTop.kicad_sch").read_text()).group(1)
    board=pcb.BOARD()
    board.SetFileName(str(BOARD))
    board.SetCopperLayerCount(2)
    board.GetDesignSettings().SetBoardThickness(pcb.FromMM(config["thickness_mm"]))
    default=board.GetDesignSettings().m_NetSettings.GetDefaultNetclass()
    default.SetClearance(pcb.FromMM(.18))
    default.SetTrackWidth(pcb.FromMM(.25))
    default.SetViaDiameter(pcb.FromMM(.65))
    default.SetViaDrill(pcb.FromMM(.3))
    title=pcb.TITLE_BLOCK()
    title.SetTitle("Numitron clock - top board")
    title.SetDate("2026-09-26")
    title.SetRevision("0.2 prototype")
    board.SetTitleBlock(title)
    ox,oy=config["board_origin_mm"]
    w,h=config["board_size_mm"]
    corners=[(ox,oy),(ox+w,oy),(ox+w,oy+h),(ox,oy+h)]
    for a,b in zip(corners,corners[1:]+corners[:1]):
        edge=pcb.PCB_SHAPE(board)
        edge.SetShape(pcb.SHAPE_T_SEGMENT)
        edge.SetStart(vec(*a)); edge.SetEnd(vec(*b)); edge.SetLayer(pcb.Edge_Cuts)
        edge.SetWidth(pcb.FromMM(.05)); board.Add(edge)
    nets={}; pad_nets={}
    for n in netlist.findall("nets/net"):
        # KiCad XML displays literal slash characters inside sheet names;
        # native PCB net names escape those embedded slashes.
        name=n.get("name").replace("/Logic / ambient light/", "/Logic {slash} ambient light/")
        net=pcb.NETINFO_ITEM(board,name); board.Add(net); nets[name]=net
        for node in n.findall("node"):
            pad_nets[(node.get("ref"),node.get("pin"))]=net
    footprints={}
    for ref,comp in components.items():
        fp=load_footprint(comp.findtext("footprint"))
        board.Add(fp); footprints[ref]=fp
        fp.SetReference(ref); fp.SetValue(comp.findtext("value"))
        fp.GetField(pcb.FIELD_T_DATASHEET).SetText(comp.findtext("datasheet",""))
        fp.GetField(pcb.FIELD_T_DESCRIPTION).SetText(comp.findtext("description",""))
        for field in comp.findall("fields/field"):
            name=field.get("name")
            if name in {"Footprint","Datasheet","Description"}:continue
            item=pcb.PCB_FIELD(fp,pcb.FIELD_T_USER,name)
            item.SetText(field.text or ""); item.SetVisible(False); item.SetLayer(pcb.F_Fab); fp.Add(item)
        fp.SetPath(pcb.KIID_PATH("/"+root_uuid+comp.find("sheetpath").get("tstamps")+comp.findtext("tstamps")))
        fp.SetSheetname(comp.find("property[@name='Sheetname']").get("value"))
        fp.SetSheetfile(comp.find("property[@name='Sheetfile']").get("value"))
        fp.SetDNP(comp.find("property[@name='dnp']") is not None)
        for p in fp.Pads():
            assert (ref,p.GetNumber()) in pad_nets, (ref,p.GetNumber())
            p.SetNet(pad_nets[(ref,p.GetNumber())])
            if ref=="U1" and p.GetNumber()=="2":p.SetLocalZoneConnection(pcb.ZONE_CONNECTION_FULL)
        x,y,angle,side=config["parts"][ref]
        if side=="B":fp.Flip(vec(0,0),pcb.FLIP_DIRECTION_LEFT_RIGHT)
        # KiCad stores a back-side footprint as mirror-Y. Add 180 degrees to
        # retain the mirror-X convention used by this placement table.
        fp.SetOrientationDegrees(angle+(180 if side=="B" else 0)); fp.SetPosition(vec(ox+x,oy+y))
        for field in fp.GetFields():
            if field.GetId()!=pcb.FIELD_T_REFERENCE:field.SetVisible(False)
        reference=fp.Reference(); reference.SetTextSize(vec(.8,.8)); reference.SetTextThickness(pcb.FromMM(.12))
        reference.SetTextAngle(pcb.EDA_ANGLE(0,pcb.DEGREES_T))
        # Start with small, legible references; final silk is reviewed after DRC.
        rx,ry=x,y-1.8
        if ref.startswith("V"):rx,ry=x,1.1
        elif ref in {"U5","U6","U7","U8"}:rx,ry=x,31
        elif ref=="J1":rx,ry=62,19
        elif ref=="U1":rx,ry=x,4
        elif ref=="U2":rx,ry=x,13
        elif ref=="U3":rx,ry=55,5.2
        elif ref.startswith("TP"):rx,ry=x,35
        elif angle in (90,270):rx,ry=x-1.6,y
        reference.SetPosition(vec(ox+rx,oy+ry))
    for ref,(x,y) in config["mounting_holes"].items():
        fp=load_footprint("Numitron:MountingHole_2.7mm_M2.5_BothSides")
        board.Add(fp); fp.SetReference(ref); fp.SetValue("M2.5 / NPTH 2.7")
        fp.SetExcludedFromBOM(True); fp.SetExcludedFromPosFiles(True)
        fp.SetPosition(vec(ox+x,oy+y)); fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
    for ref,role in config["roles"].items():
        x,y,_,_=config["parts"][ref]
        text(board,role,ox+x,oy+24.65,pcb.F_SilkS,1.05,.15)
    text(board,"NUMITRON TOP / REV 0.2",ox+55,oy+30.5,pcb.F_SilkS,1,.15)
    text(board,"PROVISIONAL SOCKETS - VERIFY FIT",ox+55,oy+32.4,pcb.F_SilkS,.8,.12)
    for ref,label in zip(["TP1","TP2","TP3","TP4","TP5"],["5V","3V3","TUBE","GND","SER"]):
        x,y,_,_=config["parts"][ref]; text(board,label,ox+x,oy+39,pcb.F_SilkS,.65,.1)
    for x,y in config["thermal_vias_mm"]:
        via=pcb.PCB_VIA(board); via.SetPosition(vec(ox+x,oy+y)); via.SetWidth(pcb.FromMM(.65))
        via.SetDrill(pcb.FromMM(.3)); via.SetViaType(pcb.VIATYPE_THROUGH); via.SetLayerPair(pcb.F_Cu,pcb.B_Cu)
        via.SetNet(nets["GND"]); board.Add(via)
    save(board)
    print(f"Placed {len(components)} schematic parts + 4 mounting holes; 6 thermal vias. No signal routing yet.")


if __name__=="__main__":main()
