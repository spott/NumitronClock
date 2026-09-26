#!/usr/bin/env python3
"""Capture the initial SOCKET-ONLY placement study using KiCad's pcbnew Python.

Requires --write; overwrites the editable PCB. Reconcile subsequent CAD edits
before regenerating. This is not the complete component placement or routing.
On macOS run with the Python bundled in the existing KiCad installation.
"""
import argparse
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware/top-board"


def v(x, y):
    return pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", required=True)
    parser.parse_args()
    project_file = PROJECT / "NumitronTop.kicad_pro"
    saved_project = project_file.read_bytes()
    placement = json.loads((PROJECT / "placement.json").read_text())
    netlist = ET.parse(ROOT / "review/NumitronTop.net.xml").getroot()
    components = {c.get("ref"): c for c in netlist.findall("components/comp")}
    root_uuid = re.search(r'\(uuid "?([0-9a-f-]+)"?\)',
                          (PROJECT / "NumitronTop.kicad_sch").read_text()).group(1)
    board = pcb.BOARD()
    board.SetCopperLayerCount(2)
    target = PROJECT / "NumitronTop.kicad_pcb"
    board.SetFileName(str(target))
    title = pcb.TITLE_BLOCK()
    title.SetTitle("Top board - socket placement study; remaining parts not placed")
    title.SetDate("2026-09-26")
    title.SetRevision("0.2 placement study")
    board.SetTitleBlock(title)
    refs = {s["reference"] for s in placement["sockets"]}
    pad_nets = {}
    for n in netlist.findall("nets/net"):
        nodes = [node for node in n.findall("node") if node.get("ref") in refs]
        if not nodes:
            continue
        net = pcb.NETINFO_ITEM(board, n.get("name"))
        board.Add(net)
        for node in nodes:
            pad_nets[(node.get("ref"), node.get("pin"))] = net

    ox, oy = placement["board_origin_mm"]
    w, h = placement["board_size_mm"]
    corners = [(ox, oy), (ox + w, oy), (ox + w, oy + h), (ox, oy + h)]
    for a, b in zip(corners, corners[1:] + corners[:1]):
        edge = pcb.PCB_SHAPE(board)
        edge.SetShape(pcb.SHAPE_T_SEGMENT)
        edge.SetStart(v(*a))
        edge.SetEnd(v(*b))
        edge.SetLayer(pcb.Edge_Cuts)
        edge.SetWidth(pcb.FromMM(0.05))
        board.Add(edge)

    for s in placement["sockets"]:
        ref = s["reference"]
        comp = components[ref]
        fpid = comp.findtext("footprint")
        library, name = fpid.split(":")
        fp = pcb.FootprintLoad(str(PROJECT / "libraries" / (library + ".pretty")), name)
        if fp is None:
            raise RuntimeError("Unable to load " + fpid)
        board.Add(fp)
        fp.SetFPIDAsString(fpid)
        fp.SetReference(ref)
        fp.SetValue(comp.findtext("value"))
        fp.GetField(pcb.FIELD_T_DATASHEET).SetText(comp.findtext("datasheet", ""))
        fp.GetField(pcb.FIELD_T_DESCRIPTION).SetText(comp.findtext("description", ""))
        for field in comp.findall("fields/field"):
            name = field.get("name")
            if name in {"Footprint", "Datasheet", "Description"}:
                continue
            item = pcb.PCB_FIELD(fp, pcb.FIELD_T_USER, name)
            item.SetText(field.text or "")
            item.SetVisible(False)
            item.SetLayer(pcb.F_Fab)
            fp.Add(item)
        path = "/" + root_uuid + comp.find("sheetpath").get("tstamps") + comp.findtext("tstamps")
        fp.SetPath(pcb.KIID_PATH(path))
        fp.SetSheetname(comp.find("sheetpath").get("names"))
        sheetfile = comp.find("property[@name='Sheetfile']")
        fp.SetSheetfile(sheetfile.get("value"))
        x, y = s["center_mm"]
        fp.SetPosition(v(ox + x, oy + y))
        for pad in fp.Pads():
            pad.SetNet(pad_nets[(ref, pad.GetNumber())])
        label = pcb.PCB_TEXT(board)
        label.SetText(s["role"])
        label.SetPosition(v(ox + x, oy + y + 12.7))
        label.SetTextSize(v(1.2, 1.2))
        label.SetTextThickness(pcb.FromMM(0.18))
        label.SetLayer(pcb.F_SilkS)
        board.Add(label)
    # Saving a newly constructed BOARD can serialize its default PROJECT and
    # overwrite the existing schematic's project settings. Preserve those.
    try:
        pcb.SaveBoard(str(target), board)
    finally:
        project_file.write_bytes(saved_project)
    print("Saved socket-only placement: 4 footprints, 36 assigned pads, 0 tracks.")


if __name__ == "__main__":
    main()
