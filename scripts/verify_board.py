#!/usr/bin/env python3
"""Read-only audit of the saved native PCB; writes only reports and a view copy."""
import collections,hashlib,json,math,xml.etree.ElementTree as ET
import pcbnew as p
from pcb_common import ROOT,PROJECT,BOARD,vec,mm,save
b=p.LoadBoard(str(BOARD));cfg=json.loads((PROJECT/'placement.json').read_text())
net=ET.parse(ROOT/'review/NumitronTop.net.xml').getroot()
comps={c.get('ref'):c for c in net.findall('components/comp')}
expected={(q.get('ref'),q.get('pin')):n.get('name').replace('/Logic / ambient light/','/Logic {slash} ambient light/') for n in net.findall('nets/net') for q in n.findall('node')}
fp={f.GetReference():f for f in b.GetFootprints()};checks=0
def check(ok,msg):
 global checks
 assert ok,msg
 checks+=1
check(set(fp)==set(comps)|set(cfg['mounting_holes']),'Component inventory')
check(b.GetCopperLayerCount()==2,'Two copper layers')
check(p.ToMM(b.GetDesignSettings().GetBoardThickness())==1.6,'Board thickness')
edges=[e for e in b.GetDrawings() if e.GetLayer()==p.Edge_Cuts]
check(len(edges)==4,'Rectangular outline')
pts={mm(e.GetStart()) for e in edges}|{mm(e.GetEnd()) for e in edges}
check(pts=={(50,50),(160,50),(160,90),(50,90)},'110 x 40 mm outline')
for ref,c in comps.items():
 f=fp[ref];check((str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName()))==c.findtext('footprint'),ref+' footprint')
 x,y,angle,face=cfg['parts'][ref]
 check(math.dist(mm(f.GetPosition()),(50+x,50+y))<.00001,ref+' position')
 check(f.IsFlipped()==(face=='B'),ref+' side')
 check(f.IsDNP()==(ref in ['R20','R21']),ref+' DNP')
 for q in f.Pads():check(q.GetNetname()==expected[(ref,q.GetNumber())],ref+'.'+q.GetNumber()+' net')
for ref in ['V1','V2','V3','V4']:
 for q in fp[ref].Pads():check(mm(q.GetSize())==(3.8,3.8) and mm(q.GetDrillSize())==(2.5,2.5),ref+' provisional land')
for q in fp['J1'].Pads():check(mm(q.GetDrillSize())==(1.1,1.1),'Header recommended drill')
check({q.GetNumber() for q in fp['U3'].Pads()}==set('123456'),'No BH1750 centre pad')
check(any(z.GetIsRuleArea() and z.GetDoNotAllowTracks() and z.GetDoNotAllowVias() and z.GetDoNotAllowPads() and z.GetDoNotAllowZoneFills() for z in fp['U3'].Zones()),'BH1750 centre keepout')
check(sum(q.GetNumber()=='2' for q in fp['U1'].Pads())==2,'Stepped regulator ground land')
for ref,xy in cfg['mounting_holes'].items():
 f=fp[ref];q=list(f.Pads())[0]
 check(q.GetAttribute()==p.PAD_ATTRIB_NPTH and mm(q.GetDrillSize())==(2.7,2.7),'M2.5 clearance hole')
 check(len(list(f.Zones()))==2,'Mounting-head copper keepouts')
tracks=list(b.GetTracks());vias=[t for t in tracks if isinstance(t,p.PCB_VIA)];wires=[t for t in tracks if not isinstance(t,p.PCB_VIA)]
check(all(t.GetWidth()>=p.FromMM(.2) for t in wires),'Minimum signal width')
check(all(not t.GetNetname().startswith('unconnected-') for t in tracks),'NC pins remain unconnected')
check(any(t.GetNetname()=='V_TUBE' and t.GetWidth()>=p.FromMM(1) and t.GetLength()>p.FromMM(50) for t in wires),'Wide filament bus')
check(any(t.GetNetname()=='+5V' and t.GetWidth()>=p.FromMM(1) and t.GetLength()>p.FromMM(15) for t in wires),'Wide input feed')
for x,y in cfg['thermal_vias_mm']:
 check(any(t.GetNetname()=='GND' and math.dist(mm(t.GetPosition()),(50+x,50+y))<.00001 for t in vias),'Regulator thermal via')
zones=[z for z in b.Zones() if not z.GetIsRuleArea()]
check(len(zones)==2 and all(z.GetNetname()=='GND' and z.HasFilledPolysForLayer(z.GetLayer()) for z in zones),'Filled ground on both faces')
report=f'''TOP-BOARD LAYOUT REVIEW — REVISION 0.2
{checks} geometry, component, net and layout checks passed.
Board: 110 x 40 mm, 2 copper layers, 1.6 mm thickness.
Parts: {len(comps)} schematic components + {len(cfg['mounting_holes'])} mounting holes.
Routing: {len(wires)} track segments; {len(vias)} through vias; 2 filled ground zones.
Schematic parity, copper clearance and complete connectivity: see board-drc.json.
Board SHA-256: {hashlib.sha256(BOARD.read_bytes()).hexdigest()}
Socket fit, decimal pin, enclosure fit, capacitor order codes and bench checks remain release hold points.
'''
(ROOT/'review/placement-checks.txt').write_text(report);print(report)
# Plotting copy: remove pours for a legible trace/assembly overview only.
for z in list(b.Zones()):
 if not z.GetIsRuleArea():b.Delete(z)
for f in b.GetFootprints():
 if f.Reference().GetLayer() in [p.F_Fab,p.B_Fab]:
  f.Reference().SetVisible(False)
 else:
  for item in list(f.GraphicalItems()):
   if isinstance(item,p.PCB_TEXT) and item.GetText()=='${REFERENCE}':f.Delete(item)
save(b,ROOT/'tmp/layout-view.kicad_pcb')
