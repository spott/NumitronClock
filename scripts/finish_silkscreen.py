#!/usr/bin/env python3
"""Place readable board legends without crowding small component lands.

Small references are shown on the assembly/Fab layers. Source of truth remains
native KiCad; this script records the initial silkscreen arrangement only.
"""
import pcbnew as pcb
from pcb_common import BOARD, vec, save, text
import argparse
_parser=argparse.ArgumentParser(description=__doc__)
_parser.add_argument("--write",action="store_true",required=True)
_parser.parse_args()
b=pcb.LoadBoard(str(BOARD))
for f in b.GetFootprints():
    ref=f.GetReference();r=f.Reference()
    if ref.startswith(('R','C')) or ref in ['U3','Q1']:
        r.SetLayer(pcb.B_Fab if f.IsFlipped() else pcb.F_Fab)
        r.SetVisible(True)
    elif ref in ['U1','U4']:
        x,y={'U1':(26.75,.9),'U4':(60.25,5.5),'Q1':(39,17.65)}[ref]
        r.SetPosition(vec(50+x,50+y))
for d in list(b.GetDrawings()):
    if isinstance(d,pcb.PCB_TEXT) and d.GetText() in ['J1 REV 0.1','1','ALS']:
        b.Delete(d)
text(b,'J1 REV 0.1',50+55,50+31,pcb.B_SilkS,.75,.12)
# Tubes face upwards; the light sensor is at the rear between digit pairs.
save(b)
print('Silkscreen references and connector pin-1 legend updated.')
