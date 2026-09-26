#!/usr/bin/env python3
"""Routing helpers, using KiCad's bundled Python; native board is authoritative.

prepare adds the documented power trunks to an unrouted placement and exports
SPECCTRA for the local Nix-provided router. import reads a local SES file.
fill adds/refills ground zones. Never run prepare on a manually routed board.
"""
import argparse
from pathlib import Path
import pcbnew as pcb
from pcb_common import ROOT, PROJECT, BOARD, vec, save, mm


def configure(board):
    settings=board.GetDesignSettings().m_NetSettings
    default=settings.GetDefaultNetclass()
    default.SetClearance(pcb.FromMM(.18)); default.SetTrackWidth(pcb.FromMM(.25))
    default.SetViaDiameter(pcb.FromMM(.65)); default.SetViaDrill(pcb.FromMM(.3))
    for name,width,nets in [('Supply',.5,['+5V','V_TUBE']),('Ground',.35,['GND'])]:
        nc=pcb.NETCLASS(name)
        nc.SetClearance(pcb.FromMM(.18)); nc.SetTrackWidth(pcb.FromMM(width))
        nc.SetViaDiameter(pcb.FromMM(.65)); nc.SetViaDrill(pcb.FromMM(.3))
        settings.SetNetclass(name,nc)
        for net in nets:
            settings.SetNetclassPatternAssignment(net,name)
            board.FindNet(net).SetNetClass(nc)


def track(board,net,points,layer,width=1.0,locked=True):
    for a,b in zip(points,points[1:]):
        if a==b:continue
        t=pcb.PCB_TRACK(board);t.SetStart(vec(a[0]+50,a[1]+50));t.SetEnd(vec(b[0]+50,b[1]+50))
        t.SetLayer(layer);t.SetWidth(pcb.FromMM(width));t.SetNet(board.FindNet(net));t.SetLocked(locked);board.Add(t)


def via(board,net,x,y,diam=.9,drill=.4):
    v=pcb.PCB_VIA(board);v.SetPosition(vec(x+50,y+50));v.SetWidth(pcb.FromMM(diam));v.SetDrill(pcb.FromMM(drill))
    v.SetViaType(pcb.VIATYPE_THROUGH);v.SetLayerPair(pcb.F_Cu,pcb.B_Cu);v.SetNet(board.FindNet(net));v.SetLocked(True);board.Add(v)


def prepare(board):
    assert all(isinstance(t,pcb.PCB_VIA) for t in board.GetTracks()), 'Existing tracks: preserve manual routing.'
    F,B=pcb.F_Cu,pcb.B_Cu
    # Feed both ribbon conductors into the regulator input through a 1 mm trunk.
    track(board,'+5V',[(53.73,23.79),(53.73,21.25),(50.5,21.25),(50.5,2.8),(49,1.3)],B)
    for x in [48.2,49]:via(board,'+5V',x,1.3)
    track(board,'+5V',[(49,1.3),(23.9,1.3)],F)
    for x in [23.9,24.7]:via(board,'+5V',x,1.3)
    track(board,'+5V',[(24.7,1.3),(23.9,1.3),(22.5,1.125)],B,.8)
    track(board,'+5V',[(24.7,1.3),(25.25,1.85),(25.25,2.35)],B,.5)
    # Local regulator output connections use 0.5 mm necks at its 0.68 mm lands.
    track(board,'V_TUBE',[(28.25,2.35),(29.3,1.3),(31,1.125)],B,.5)
    track(board,'V_TUBE',[(29.3,1.3),(29.2,1.4),(29.2,6.875),(28.225,7.85)],B,.5)
    track(board,'V_TUBE',[(28.225,7.85),(27.5,8.575),(27.5,10.4)],B,.65)
    via(board,'V_TUBE',27.5,10.4)
    via(board,'V_TUBE',27.5,11.2)
    track(board,'V_TUBE',[(27.5,10.4),(27.5,11.2)],B,.8)
    track(board,'V_TUBE',[(27.5,10.4),(27.5,11.2),(26.75,11.95),(26.75,25.75),(107,25.75)],F)
    # Common-positive tube feed. All segment returns remain independently routed.
    for cx,end in [(14.5,26),(39,50.5),(71,82.5),(95.5,107)]:
        px,py=cx+8.559509,15.781153
        track(board,'V_TUBE',[(px,py),(end,py+end-px),(end,25.75)],F,1.0)
    track(board,'V_TUBE',[(26,25.75),(26.75,25.75)],F)
    save(board)


def fill(board):
    existing={z.GetLayer() for z in board.Zones() if not z.GetIsRuleArea()}
    for layer in [pcb.F_Cu,pcb.B_Cu]:
        if layer in existing:continue
        z=pcb.ZONE(board);z.SetLayer(layer);z.SetNet(board.FindNet('GND'))
        z.SetLocalClearance(pcb.FromMM(.25));z.SetThermalReliefGap(pcb.FromMM(.25));z.SetThermalReliefSpokeWidth(pcb.FromMM(.35))
        z.SetMinThickness(pcb.FromMM(.2));z.SetPadConnection(pcb.ZONE_CONNECTION_THERMAL)
        z.SetIslandRemovalMode(pcb.ISLAND_REMOVAL_MODE_ALWAYS)
        z.Outline().NewOutline()
        for x,y in [(50.5,50.5),(159.5,50.5),(159.5,89.5),(50.5,89.5)]:z.Outline().Append(pcb.FromMM(x),pcb.FromMM(y))
        board.Add(z)
    board.BuildConnectivity()
    pcb.ZONE_FILLER(board).Fill(board.Zones())
    save(board)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','export','import','fill']);ap.add_argument('--file',type=Path)
    a=ap.parse_args();board=pcb.LoadBoard(str(BOARD));configure(board)
    if a.action=='prepare':prepare(board)
    if a.action in ['prepare','export']:
        destination=a.file or ROOT/'tmp/NumitronTop.dsn'
        assert pcb.ExportSpecctraDSN(board,str(destination));print('Exported',destination)
    elif a.action=='import':
        assert a.file and pcb.ImportSpecctraSES(board,str(a.file));save(board);print('Imported',a.file)
    elif a.action=='fill':fill(board)


if __name__=='__main__':main()
