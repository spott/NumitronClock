#!/usr/bin/env python3
"""Create a review BOM from the native KiCad XML netlist, not the capture script."""
from collections import defaultdict
from pathlib import Path
import re
import xml.etree.ElementTree as ET

root=Path(__file__).resolve().parents[1]
tree=ET.parse(root/"review/NumitronTop.net.xml").getroot()
groups=defaultdict(list)
for c in tree.find("components"):
    ref=c.attrib["ref"]
    if ref.startswith("TP"): continue
    fields={f.attrib["name"]:(f.text or "") for f in c.findall("fields/field")}
    dnp=any(p.attrib.get("name")=="dnp" for p in c.findall("property"))
    key=(c.findtext("value"),fields.get("MPN",""),c.findtext("footprint") or "HOLD",dnp,c.findtext("datasheet") or "")
    groups[key].append(ref)
def sortref(ref):
    m=re.fullmatch(r"([A-Z]+)(\d+)",ref)
    return m[1],int(m[2])
lines=["# Preliminary top-board BOM","",
       "Revision 0.1. Generated from the exported native KiCad netlist by `scripts/update_bom.py`. Quantities are for one top board. This is a review BOM, not an order or an assembly release.","",
       "| References | Qty | Value / function | Manufacturer part number | Footprint | Assembly | Datasheet |",
       "|---|---:|---|---|---|---|---|"]
for (value,mpn,fp,dnp,ds),refs in sorted(groups.items(),key=lambda item:sortref(sorted(item[1],key=sortref)[0])):
    refs=sorted(refs,key=sortref)
    file=Path(ds).name
    order=mpn or "KYOCERA AVX X7R family; exact order code pending"
    assembly="DNP" if dnp else ("Tubes in hand; sockets separate below" if refs[0].startswith("V") else "Fit")
    lines.append(f"| {', '.join(refs)} | {len(refs)} | {value} | {order} | {fp} | {assembly} | [PDF](../datasheets/{file}) |")
lines += ["","## Mechanical and cable items","",
          "| Item | Quantity | Selection / status |","|---|---:|---|",
          "| Tube sockets | 4 | Ordered GZC9-A, [Amazon B0BGBJ7L41](https://www.amazon.com/dp/B0BGBJ7L41). [Drawing](../datasheets/GZC9-A_socket-dimensions.jpg) archived; [provisional footprint assumptions](socket.md) authorized 2026-09-25. Assigned to V1-V4 for layout; check physical fit before ordering. |",
          "| Cable female connectors | 2 | Wurth 61201623021, [datasheet](../datasheets/idc-socket.pdf). One at each cable end. |",
          "| Strain-relief caps | 2 | Included in the selected Wurth socket's with-strain-relief specification; confirm supplied pieces and assembled clearance. |",
          "| Ribbon cable | ~150 mm initially | 3M 3365/16, 28 AWG, 1.27 mm pitch, [datasheet](../datasheets/3m-3365-ribbon.pdf). Final length follows the debugging/enclosure clearance check. |",
          "| Board spacers / screws | TBD | Target 25-30 mm separation. Mounting-hole count and positions await mechanical fit. |","",
          "TP1-TP5 are bare PCB test pads; they require no purchased components. The bottom-board mate of J1 is outside this top-board BOM.","",
          "## Assembly notes","",
          "- R20/R21 are omitted when the bottom board supplies the I2C pull-ups. All selected resistors are Yageo RC0603, 1%, 0.1 W; individual part specifications are archived.",
          "- Capacitor footprint sizes, voltage ratings and dielectric are specified, but exact order codes remain pending. Select from the archived KYOCERA AVX X7R family, and verify effective capacitance at bias before freezing the BOM. C2+C3 must retain at least 2.2 uF total.",
          "- V1-V4 use Numitron:GZC9-A_B9A_Provisional: assumed 0.5 mm terminal thickness, 18 mm pad circle, 2.5 mm plated holes and 3.8 mm copper pads. The owner authorized using these estimates for layout; verify fit before ordering.",
          "- U3's WSOF6I land pattern remains to be assigned, with no soldered center pad.",
          "- U1's C507885 identifier comes from the Obsidian plan. Stock, price, assembly-house availability and substitutions have not been qualified.",
          "- Use normal-pinout TLV809EA29DBZR, not an R/V pinout variant. Use AHCT logic, not HC. The four TPIC parts use the wide SOIC-20 package.",""]
(root/"docs/bom.md").write_text("\n".join(lines))
print(f"Wrote BOM: {len(groups)} electrical line items.")
