#!/usr/bin/env python3
"""Validate archived component documents and refresh provenance. Never downloads."""
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
    "rohm-wsof6-package.pdf": ("ROHM WSOF6 mounting reference; WSOF6I correspondence remains to be checked for U3", "https://fscdn.rohm.com/en/techdata_basic/ic/package/Jisso_WSOF6-1-2_Rev005s_TR%28MSL3%29.pdf"),
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
image_sources={
    "GZC9-A_socket-dimensions.jpg": {
        "description": "GZC9-A socket dimension drawing; supplied by owner, manufacturer unidentified",
        "source_url": "https://www.amazon.com/dp/B0BGBJ7L41",
        "source_kind": "user-provided attachment associated with the ordered listing",
        "original_filename": "61KVbbJ96SL._AC_SL1300_.jpg",
        "received": "2026-09-21",
        "media_type": "image/jpeg",
    },
}
assert {p.name for p in directory.iterdir() if p.suffix.lower() in {".pdf",".jpg"}}==set(sources)|set(image_sources), "Document/source manifest mismatch"
records=[]
retrieved_dates={"rohm-wsof6-package.pdf":"2026-09-26"}
for filename,(description,url) in sorted(sources.items()):
    path=directory/filename
    data=path.read_bytes()
    assert data.startswith(b"%PDF"), f"Non-PDF response: {filename}"
    reader=PdfReader(path,strict=True)
    assert len(reader.pages)>0
    records.append({"file":filename,"description":description,"source_url":url,"retrieved":retrieved_dates.get(filename,"2026-09-18"),"pages":len(reader.pages),"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()})
for filename,metadata in image_sources.items():
    data=(directory/filename).read_bytes()
    assert data.startswith(b"\xff\xd8\xff") and data.endswith(b"\xff\xd9"), f"Not a complete JPEG: {filename}"
    records.append({"file":filename,**metadata,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()})
records.sort(key=lambda r:r["file"])
(directory/"sources.json").write_text(json.dumps(records,indent=2)+"\n")
(directory/"SHA256SUMS").write_text("".join(f'{r["sha256"]}  {r["file"]}\n' for r in records))
lines=["# Archived component datasheets","",f"{len(sources)} original PDF documents and {len(image_sources)} owner-provided JPEG drawing. The original files are committed with the design. Copyright and ownership remain with their respective publishers. Source URLs, individual receipt dates and SHA-256 hashes are in [sources.json](sources.json); [SHA256SUMS](SHA256SUMS) provides a compact integrity list.","",
       "| Local document | Applies to | Pages / format | Source or associated listing |","|---|---|---:|---|"]
for r in records: lines.append(f'| [{r["file"]}]({r["file"]}) | {r["description"]} | {r.get("pages","JPEG")} | [Source]({r["source_url"]}) |')
lines += ["","## Known discrepancies and missing mechanical data","",
          "- **Tube identity:** the owner confirms DR2000-marked tubes with visible prefix decimals. RCA's archived table assigns pin 1 to a decimal on DR2010 and NC on DR2000. Preserve the owner's observation; verify the actual pin-1 connection before enabling the separator.",
          "- **TPIC6B595:** Rev. D's pin-function table lists SRCK as pin 15. The package drawing and application circuit show **pin 13**; pin 15 is DRAIN5. The schematic uses pin 13.",
          "- **GZC9-A socket:** the owner supplied the [listing dimension drawing](GZC9-A_socket-dimensions.jpg) on 2026-09-21. It is preserved byte for byte. On 2026-09-25 the owner authorized a provisional footprint: assume 0.5 mm terminal thickness and an 18 mm pad circle; use 2.5 mm plated holes. [Socket notes](../docs/socket.md) distinguish drawing data from estimates. Physical fit and numbering checks are deferred until before ordering and do not block layout.",
          "- **Capacitors:** the family PDF is included. Exact C1-C15 order codes and biased capacitance are not yet frozen.","",
          "Run `nix develop --command python3 scripts/index_datasheets.py` to validate PDF parsing and JPEG file markers, and refresh hashes after deliberately adding or replacing a source. Visually inspect new drawings as well. Do not replace a source silently; review its changed pin tables/specifications and commit the new document together with the design consequences.",""]
(directory/"README.md").write_text("\n".join(lines))
print(f"Indexed {len(sources)} PDFs ({sum(r.get('pages',0) for r in records)} pages) and {len(image_sources)} JPEG drawing(s).")
