# Archived component datasheets

21 original PDF documents and 1 owner-provided JPEG drawing. The original files are committed with the design. Copyright and ownership remain with their respective publishers. Source URLs, individual receipt dates and SHA-256 hashes are in [sources.json](sources.json); [SHA256SUMS](SHA256SUMS) provides a compact integrity list.

| Local document | Applies to | Pages / format | Source or associated listing |
|---|---|---:|---|
| [3m-3365-ribbon.pdf](3m-3365-ribbon.pdf) | 3M 3365 series; 3365/16 ribbon cable | 5 | [Source](https://multimedia.3m.com/mws/media/22052O/3mtm-round-conductor-flat-cable-050in-3365-series-ts0080.pdf) |
| [AP7361C.pdf](AP7361C.pdf) | Diodes AP7361C; U1 | 22 | [Source](https://www.diodes.com/assets/Datasheets/AP7361C.pdf) |
| [GZC9-A_socket-dimensions.jpg](GZC9-A_socket-dimensions.jpg) | GZC9-A socket dimension drawing; supplied by owner, manufacturer unidentified | JPEG | [Source](https://www.amazon.com/dp/B0BGBJ7L41) |
| [RC0603FR-07100KL.pdf](RC0603FR-07100KL.pdf) | Yageo RC0603FR-07100KL; individual resistor specification | 1 | [Source](https://www.yageogroup.com/component-documentation/download/specsheet/RC0603FR-07100KL) |
| [RC0603FR-0710KL.pdf](RC0603FR-0710KL.pdf) | Yageo RC0603FR-0710KL; individual resistor specification | 1 | [Source](https://www.yageogroup.com/component-documentation/download/specsheet/RC0603FR-0710KL) |
| [RC0603FR-071KL.pdf](RC0603FR-071KL.pdf) | Yageo RC0603FR-071KL; individual resistor specification | 1 | [Source](https://www.yageogroup.com/component-documentation/download/specsheet/RC0603FR-071KL) |
| [RC0603FR-072K2L.pdf](RC0603FR-072K2L.pdf) | Yageo RC0603FR-072K2L; individual resistor specification | 1 | [Source](https://www.yageogroup.com/component-documentation/download/specsheet/RC0603FR-072K2L) |
| [RC0603FR-0733RL.pdf](RC0603FR-0733RL.pdf) | Yageo RC0603FR-0733RL; individual resistor specification | 1 | [Source](https://www.yageogroup.com/component-documentation/download/specsheet/RC0603FR-0733RL) |
| [RC0603FR-0746K4L.pdf](RC0603FR-0746K4L.pdf) | Yageo RC0603FR-0746K4L; individual resistor specification | 1 | [Source](https://www.yageogroup.com/component-documentation/download/specsheet/RC0603FR-0746K4L) |
| [RC0603FR-074K7L.pdf](RC0603FR-074K7L.pdf) | Yageo RC0603FR-074K7L; individual resistor specification | 1 | [Source](https://www.yageogroup.com/component-documentation/download/specsheet/RC0603FR-074K7L) |
| [avx-x7r.pdf](avx-x7r.pdf) | KYOCERA AVX KGM X7R family; C1-C15 selection reference | 4 | [Source](https://datasheets.kyocera-avx.com/KGM_X7R.pdf) |
| [bh1750fvi.pdf](bh1750fvi.pdf) | ROHM BH1750FVI; U3 (manufacturer PDF hosted by DigiKey) | 20 | [Source](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/6165/bh1750fvi-e.pdf) |
| [dr2000.pdf](dr2000.pdf) | RCA Numitron family; V1-V4 (original RCA document hosted by The Valve Museum) | 12 | [Source](https://www.r-type.org/pdfs/dr2000.pdf) |
| [es100.pdf](es100.pdf) | Everset ES100 v0.97; WWVB test driver register and timing reference | 26 | [Source](https://everset.tech/wp-content/uploads/2014/11/ES100DataSheetver0p97.pdf) |
| [idc-header.pdf](idc-header.pdf) | Wurth 61201621621; J1 | 8 | [Source](https://www.we-online.com/components/products/datasheet/61201621621.pdf) |
| [idc-socket.pdf](idc-socket.pdf) | Wurth 61201623021; cable sockets with strain relief | 6 | [Source](https://www.we-online.com/components/products/datasheet/61201623021.pdf) |
| [mmbt3904.pdf](mmbt3904.pdf) | Diodes MMBT3904; Q1 | 7 | [Source](https://www.diodes.com/datasheet/download/MMBT3904.pdf) |
| [rohm-wsof6-package.pdf](rohm-wsof6-package.pdf) | ROHM WSOF6 mounting reference; adapted for U3 WSOF6I as documented in docs/placement.md | 11 | [Source](https://fscdn.rohm.com/en/techdata_basic/ic/package/Jisso_WSOF6-1-2_Rev005s_TR%28MSL3%29.pdf) |
| [rp2350-datasheet.pdf](rp2350-datasheet.pdf) | Raspberry Pi RP2350; bottom-board interface reference, including A2 erratum E9 | 1380 | [Source](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf) |
| [sn74ahct125.pdf](sn74ahct125.pdf) | TI SN74AHCT125; U2 | 41 | [Source](https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf) |
| [tlv809e.pdf](tlv809e.pdf) | TI TLV809E family; U4 | 52 | [Source](https://www.ti.com/lit/ds/symlink/tlv809e.pdf) |
| [tpic6b595.pdf](tpic6b595.pdf) | TI TPIC6B595; U5-U8 | 28 | [Source](https://www.ti.com/lit/ds/symlink/tpic6b595.pdf) |

## Known discrepancies and missing mechanical data

- **Tube identity:** the owner confirms DR2000-marked tubes with visible prefix decimals. RCA's archived table assigns pin 1 to a decimal on DR2010 and NC on DR2000. Preserve the owner's observation; verify the actual pin-1 connection before enabling the separator.
- **TPIC6B595:** Rev. D's pin-function table lists SRCK as pin 15. The package drawing and application circuit show **pin 13**; pin 15 is DRAIN5. The schematic uses pin 13.
- **GZC9-A socket:** the owner supplied the [listing dimension drawing](GZC9-A_socket-dimensions.jpg) on 2026-09-21. It is preserved byte for byte. On 2026-09-25 the owner authorized a provisional footprint: assume 0.5 mm terminal thickness and an 18 mm pad circle; use 2.5 mm plated holes. [Socket notes](../docs/socket.md) distinguish drawing data from estimates. Physical fit and numbering checks are deferred until before ordering and do not block layout.
- **Capacitors:** the family PDF is included. Exact C1-C15 order codes and biased capacitance are not yet frozen.

Run `nix develop --command python3 scripts/index_datasheets.py` to validate PDF parsing and JPEG file markers, and refresh hashes after deliberately adding or replacing a source. Visually inspect new drawings as well. Do not replace a source silently; review its changed pin tables/specifications and commit the new document together with the design consequences.
