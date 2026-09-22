# Preliminary top-board BOM

Revision 0.1. Generated from the exported native KiCad netlist by `scripts/update_bom.py`. Quantities are for one top board. This is a review BOM, not an order or an assembly release.

| References | Qty | Value / function | Manufacturer part number | Footprint | Assembly | Datasheet |
|---|---:|---|---|---|---|---|
| C1, C2, C3 | 3 | 10u 25V X7R | KYOCERA AVX X7R family; exact order code pending | Capacitor_SMD:C_1206_3216Metric | Fit | [PDF](../datasheets/avx-x7r.pdf) |
| C4, C5, C6, C7, C8, C10, C12, C14 | 8 | 100n 50V X7R | KYOCERA AVX X7R family; exact order code pending | Capacitor_SMD:C_0603_1608Metric | Fit | [PDF](../datasheets/avx-x7r.pdf) |
| C9, C11, C13, C15 | 4 | 1u 25V X7R | KYOCERA AVX X7R family; exact order code pending | Capacitor_SMD:C_0805_2012Metric | Fit | [PDF](../datasheets/avx-x7r.pdf) |
| J1 | 1 | 61201621621 | 61201621621 | Connector_IDC:IDC-Header_2x08_P2.54mm_Vertical | Fit | [PDF](../datasheets/idc-header.pdf) |
| Q1 | 1 | MMBT3904-7-F | MMBT3904-7-F | Package_TO_SOT_SMD:SOT-23 | Fit | [PDF](../datasheets/mmbt3904.pdf) |
| R1 | 1 | 46.4k 1% | RC0603FR-0746K4L | Resistor_SMD:R_0603_1608Metric | Fit | [PDF](../datasheets/RC0603FR-0746K4L.pdf) |
| R2 | 1 | 10k 1% | RC0603FR-0710KL | Resistor_SMD:R_0603_1608Metric | Fit | [PDF](../datasheets/RC0603FR-0710KL.pdf) |
| R3, R4, R5, R6 | 4 | 33R | RC0603FR-0733RL | Resistor_SMD:R_0603_1608Metric | Fit | [PDF](../datasheets/RC0603FR-0733RL.pdf) |
| R7, R8, R9 | 3 | 100k | RC0603FR-07100KL | Resistor_SMD:R_0603_1608Metric | Fit | [PDF](../datasheets/RC0603FR-07100KL.pdf) |
| R10, R16 | 2 | 2.2k | RC0603FR-072K2L | Resistor_SMD:R_0603_1608Metric | Fit | [PDF](../datasheets/RC0603FR-072K2L.pdf) |
| R11, R12, R13, R14, R17 | 5 | 4.7k | RC0603FR-074K7L | Resistor_SMD:R_0603_1608Metric | Fit | [PDF](../datasheets/RC0603FR-074K7L.pdf) |
| R15, R18 | 2 | 1k | RC0603FR-071KL | Resistor_SMD:R_0603_1608Metric | Fit | [PDF](../datasheets/RC0603FR-071KL.pdf) |
| R19 | 1 | 10k | RC0603FR-0710KL | Resistor_SMD:R_0603_1608Metric | Fit | [PDF](../datasheets/RC0603FR-0710KL.pdf) |
| R20, R21 | 2 | 4.7k | RC0603FR-074K7L | Resistor_SMD:R_0603_1608Metric | DNP | [PDF](../datasheets/RC0603FR-074K7L.pdf) |
| U1 | 1 | AP7361C-Y5-13 | AP7361C-Y5-13 | Package_TO_SOT_SMD:SOT-89-5 | Fit | [PDF](../datasheets/AP7361C.pdf) |
| U2 | 1 | SN74AHCT125DR | SN74AHCT125DR | Package_SO:SOIC-14_3.9x8.7mm_P1.27mm | Fit | [PDF](../datasheets/sn74ahct125.pdf) |
| U3 | 1 | BH1750FVI-TR | BH1750FVI-TR | HOLD | Fit | [PDF](../datasheets/bh1750fvi.pdf) |
| U4 | 1 | TLV809EA29DBZR | TLV809EA29DBZR | Package_TO_SOT_SMD:SOT-23 | Fit | [PDF](../datasheets/tlv809e.pdf) |
| U5, U6, U7, U8 | 4 | TPIC6B595DWR | TPIC6B595DWR | Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm | Fit | [PDF](../datasheets/tpic6b595.pdf) |
| V1, V2, V3, V4 | 4 | DR2000 / GZC9-A | DR2000 | HOLD | Tubes in hand; sockets separate below | [PDF](../datasheets/dr2000.pdf) |

## Mechanical and cable items

| Item | Quantity | Selection / status |
|---|---:|---|
| Tube sockets | 4 | Ordered GZC9-A, [Amazon B0BGBJ7L41](https://www.amazon.com/dp/B0BGBJ7L41). [Dimension drawing](../datasheets/GZC9-A_socket-dimensions.jpg) received from owner 2026-09-21; [remaining terminal and numbering checks](socket.md) precede footprint assignment. Socket footprint belongs to V1-V4's tube/socket assembly. |
| Cable female connectors | 2 | Wurth 61201623021, [datasheet](../datasheets/idc-socket.pdf). One at each cable end. |
| Strain-relief caps | 2 | Included in the selected Wurth socket's with-strain-relief specification; confirm supplied pieces and assembled clearance. |
| Ribbon cable | ~150 mm initially | 3M 3365/16, 28 AWG, 1.27 mm pitch, [datasheet](../datasheets/3m-3365-ribbon.pdf). Final length follows the debugging/enclosure clearance check. |
| Board spacers / screws | TBD | Target 25-30 mm separation. Mounting-hole count and positions await mechanical fit. |

TP1-TP5 are bare PCB test pads; they require no purchased components. The bottom-board mate of J1 is outside this top-board BOM.

## Assembly notes

- R20/R21 are omitted when the bottom board supplies the I2C pull-ups. All selected resistors are Yageo RC0603, 1%, 0.1 W; individual part specifications are archived.
- Capacitor footprint sizes, voltage ratings and dielectric are specified, but exact order codes remain pending. Select from the archived KYOCERA AVX X7R family, and verify effective capacitance at bias before freezing the BOM. C2+C3 must retain at least 2.2 uF total.
- U3 and V1-V4 deliberately have no assigned footprint. The sensor requires the correct WSOF6I lands with no soldered center pad; socket drill geometry must come from the ordered samples.
- U1's C507885 identifier comes from the Obsidian plan. Stock, price, assembly-house availability and substitutions have not been qualified.
- Use normal-pinout TLV809EA29DBZR, not an R/V pinout variant. Use AHCT logic, not HC. The four TPIC parts use the wide SOIC-20 package.
