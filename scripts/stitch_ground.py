#!/usr/bin/env python3
"""Initial ground stitching; native CAD remains authoritative after edits.

Places vias only where native pad/track shapes clear both layers. Refill zones
and run the full DRC afterwards. Never treats this geometric pass as DRC.
"""
import math
import pcbnew as p
from pcb_common import BOARD,save,vec,mm
from route_board import via
import argparse
_parser=argparse.ArgumentParser(description=__doc__)
_parser.add_argument("--write",action="store_true",required=True)
_parser.parse_args()
b=p.LoadBoard(str(BOARD));F,B=p.F_Cu,p.B_Cu
pads=[q for f in b.GetFootprints() for q in f.Pads()]
tracks=list(b.GetTracks());shapes=[];samepads=[];holes=[];existing=[]
for q in pads:
 dr=q.GetDrillSize().x
 if dr:holes.append((q.GetPosition(),dr/2))
 for layer in [F,B]:
  if not q.IsOnLayer(layer):continue
  s=q.GetEffectiveShape(layer)
  if q.GetNetname()!='GND':shapes.append((s,p.FromMM(.25 if q.GetAttribute()==p.PAD_ATTRIB_NPTH else .2)))
  elif not dr:samepads.append(s)
for t in tracks:
 if isinstance(t,p.PCB_VIA):
  holes.append((t.GetPosition(),t.GetDrillValue()/2))
  if t.GetNetname()=='GND':existing.append(t.GetPosition())
 if t.GetNetname()!='GND':
  for layer in [F,B]:
   if t.IsOnLayer(layer):shapes.append((t.GetEffectiveShape(layer),p.FromMM(.2)))
for f in b.GetFootprints():
 for z in f.Zones():
  if z.GetIsRuleArea():shapes.append((z.Outline(),0))
# Keep vias away from the proposed M2.5 heads on both faces.
mount=[vec(x+50,y+50) for x,y in [(3,3),(107,3),(3,37),(107,37)]]
added=[]
def add(x,y,spacing=2.0):
 pt=vec(x,y)
 if not (50.95<=x<=159.05 and 50.95<=y<=89.05):return False
 if any((pt.x-h.x)**2+(pt.y-h.y)**2<p.FromMM(2.95+.325)**2 for h in mount):return False
 if any((pt.x-h.x)**2+(pt.y-h.y)**2<p.FromMM(spacing)**2 for h in existing):return False
 if any(s.Collide(pt,c+p.FromMM(.325)) for s,c in shapes):return False
 if any(s.Collide(pt,p.FromMM(.325+.15)) for s in samepads):return False
 if any((pt.x-h.x)**2+(pt.y-h.y)**2<(r+p.FromMM(.15+.25))**2 for h,r in holes):return False
 via(b,'GND',x-50,y-50,.65,.3);existing.append(pt);holes.append((pt,p.FromMM(.15)));added.append((round(x-50,3),round(y-50,3)));return True
for q in pads:
 if q.GetNetname()!='GND':continue
 x,y=mm(q.GetPosition())
 for radius in [1.1,1.4,1.7,2.0,2.4]:
  if any(add(round(x+radius*math.cos(a*math.pi/4),2),round(y+radius*math.sin(a*math.pi/4),2)) for a in range(8)):break
for x in range(57,156,10):
 for y in range(57,87,10):add(x,y,4.0)
# Reflowed SMD grounds connect directly to their local copper; the IDC through
# holes retain thermal relief for hand soldering.
for z in b.Zones():
 if not z.GetIsRuleArea():z.SetPadConnection(p.ZONE_CONNECTION_THT_THERMAL)
for f in b.GetFootprints():
 if f.GetReference()=='J1':
  for q in f.Pads():
   if q.GetNetname()=='GND':q.SetThermalSpokeAngle(p.EDA_ANGLE(90,p.DEGREES_T));q.SetThermalGap(p.FromMM(.2))
save(b)
print('Added',len(added),'ground vias:',added)
