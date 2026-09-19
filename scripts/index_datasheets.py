#!/usr/bin/env python3
"""Validate archived PDFs and refresh their provenance index. Never downloads."""
from pathlib import Path
import hashlib
import json
from pypdf import PdfReader

root=Path(__file__).resolve().parents[1]
directory=root/"datasheets"
sources={
    "AP7361C.pdf": ("Diodes AP7361C; U1", "https://www.diodes.com/assets/Datasheets/AP7361C.pdf"),
    "tpic6b595.pdf": ("TI TPIC6B595; U5-U8", "https://www.ti.com/lit/ds/symlink/tpic6b595.pdf"),
    "sn74ahct125.pdf": ("TI SN74AHCT125; U2", "https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf"),
    "bh1750fvi.pdf": ("ROHM BH1750FVI; U3 (manufacturer PDF hosted by DigiKey)", "https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/6165/bh1750fvi-e.pdf"),
    "tlv809e.pdf": ("TI TLV809E family; U4", "https://www.ti.com/lit/ds/symlink/tlv809e.pdf"),
    "mmbt3904.pdf": ("Diodes MMBT3904; Q1", "https://www.diodes.com/datasheet/download/MMBT3904.pdf"),
    "dr2000.pdf": ("RCA Numitron family; V1-V4 (original RCA document hosted by The Valve Museum)", "https://www.r-type.org/pdfs/dr2000.pdf"),
    "idc-header.pdf": ("Wurth 61201621621; J1", "https://www.we-online.com/components/products/datasheet/61201621621.pdf"),
    "idc-socket.pdf": ("Wurth 61201623021; cable sockets with strain relief", "https://www.we-online.com/components/products/datasheet/61201623021.pdf"),
    "avx-x7r.pdf": ("KYOCERA AVX KGM X7R family; C1-C15 selection reference", "https://datasheets.kyocera-avx.com/KGM_X7R.pdf"),
    "3m-3365-ribbon.pdf": ("3M 3365 series; 3365/16 ribbon cable", "https://multimedia.3m.com/mws/media/22052O/3mtm-round-conductor-flat-cable-050in-3365-series-ts0080.pdf"),
    "rp2350-datasheet.pdf": ("Raspberry Pi RP2350; bottom-board interface reference, including A2 erratum E9", "https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf"),
}
for code in ["46K4","10K","33R","100K","4K7","2K2","1K"]:
    part="RC0603FR-07"+code+"L"
    sources[part+".pdf"]=("Yageo "+part+"; individual resistor specification", "https://www.yageogroup.com/component-documentation/download/specsheet/"+part)
assert {p.name for p in directory.glob("*.pdf")}==set(sources), "PDF/source manifest mismatch"
records=[]
for filename,(description,url) in sorted(sources.items()):
    path=directory/filename
    data=path.read_bytes()
    assert data.startswith(b"%PDF"), f"Non-PDF response: {filename}"
    reader=PdfReader(path,strict=True)
    assert len(reader.pages)>0
    records.append({"file":filename,"description":description,"source_url":url,"retrieved":"2026-09-18","pages":len(reader.pages),"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()})
(directory/"sources.json").write_text(json.dumps(records,indent=2)+"\n")
(directory/"SHA256SUMS").write_text("".join(f'{r["sha256"]}  {r["file"]}\n' for r in records))
lines=["# Archived component datasheets","",f"{len(records)} original PDF documents, retrieved 2026-09-18 and committed with the design. Copyright and ownership remain with their respective publishers. Source URLs and SHA-256 hashes are in [sources.json](sources.json); [SHA256SUMS](SHA256SUMS) provides a compact integrity list.","",
       "| Local document | Applies to | Pages | Original source |","|---|---|---:|---|"]
for r in records: lines.append(f'| [{r["file"]}]({r["file"]}) | {r["description"]} | {r["pages"]} | [Source]({r["source_url"]}) |')
lines += ["","## Known discrepancies and missing mechanical data","",
          "- **Tube identity:** the owner confirms DR2000-marked tubes with visible prefix decimals. RCA's archived table assigns pin 1 to a decimal on DR2010 and NC on DR2000. Preserve the owner's observation; verify the actual pin-1 connection before enabling the separator.",
          "- **TPIC6B595:** Rev. D's pin-function table lists SRCK as pin 15. The package drawing and application circuit show **pin 13**; pin 15 is DRAIN5. The schematic uses pin 13.",
          "- **GZC9-A socket:** ordered listing [B0BGBJ7L41](https://www.amazon.com/dp/B0BGBJ7L41), supplied by the owner as [this short link](https://a.co/d/02oJ9ki1). The link resolved, but the listing/drawing could not be retrieved. No manufacturer PDF or verified drill drawing is available in this archive. Measurements from the ordered samples are still required; the tube's pin circle is not a substitute for socket-tail geometry.",
          "- **Capacitors:** the family PDF is included. Exact C1-C15 order codes and biased capacitance are not yet frozen.","",
          "Run `nix develop --command python3 scripts/index_datasheets.py` to verify PDF parsing and refresh hashes after deliberately adding or replacing a source. Do not replace a source silently; review its changed pin tables/specifications and commit the new document together with the design consequences.",""]
(directory/"README.md").write_text("\n".join(lines))
print(f"Validated and indexed {len(records)} PDFs ({sum(r['pages'] for r in records)} pages).")
