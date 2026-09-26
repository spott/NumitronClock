# GZC9-A socket dimensions

The owner supplied this drawing on 2026-09-21 for the ordered [Amazon B0BGBJ7L41 sockets](https://www.amazon.com/dp/B0BGBJ7L41). The [original JPEG](../datasheets/GZC9-A_socket-dimensions.jpg) is archived unchanged, with its original filename, receipt date and SHA-256 hash in [the source index](../datasheets/sources.json). The drawing identifies the part as GZC9-A but gives no manufacturer or revision.

![Owner-provided GZC9-A dimension drawing](../datasheets/GZC9-A_socket-dimensions.jpg)

## Dimensions shown

Dimensions below are interpreted in millimetres, consistent with the project plan. The image itself has no unit note. Values are transcribed from callouts, not measured from image pixels.

| Feature | Drawing callout | Use / interpretation |
|---|---|---|
| Socket body outside diameter | 18 ±0.5 | Allow up to 18.5 mm for the body before placement clearance. |
| Body axial depth | 9 ±0.5 | Body envelope above its rear face; installed height also depends on seating. |
| Overall axial length, including terminals | 15 ±0.5 | Nominal terminal projection is 6 mm beyond the body. |
| Contact circle in the face view | Ø12 ±0.2 | Tube-contact pattern; the side view shows the terminals bending outward. |
| Terminal span in the side view | 18 ±0.5 | The left-side dimension across the projected terminals; it is not explicitly labelled as a PCB pitch-circle diameter. |
| Narrow terminal section, visible width | 2 ±0.1 | One cross-section dimension; the perpendicular metal thickness is not supplied. |
| Straight end section of a terminal | 4 ±0.1 | Axial length of the narrow section. |
| Two central circular features | Ø6 and Ø3.5 | Neither callout establishes a required PCB hole. |

The nominal projection follows from 15 − 9 = 6 mm. Taking the two stated tolerances independently gives 5–7 mm; this is a conservative envelope calculation, not a separately specified seating dimension. Keep the space below the socket clear of components until its seating and PCB thickness are resolved.

## Provisional footprint for layout

On **2026-09-25 the owner authorized proceeding from this drawing with an estimated pin thickness**. `Numitron:GZC9-A_B9A_Provisional` is now assigned to V1–V4. Physical checks below are deferred until before PCB ordering and do not prevent top-board placement or routing.

| Working parameter | Value | Basis |
|---|---|---|
| Terminal thickness | **0.5 mm** | Engineering estimate requested by the owner; not given in the drawing. |
| Terminal width | 2.0 ±0.1 mm | Drawing callout. |
| PCB pad circle | **Ø18 mm** | Working interpretation of the side-view 18 mm terminal span; not a verified pitch-circle dimension. |
| Pin positions | Nine positions at **36° steps**, with a **72° indexing gap** | Assumed B9A/Noval pattern, consistent with the illustrated face view. |
| Finished plated holes | **Ø2.5 mm**, round | Allows the assumed flat terminal to pass through without requiring routed slots. |
| Copper pads | **3.8 × 3.8 mm**; pin 1 square, others round | 0.65 mm nominal annular ring at the narrowest point. |
| Front courtyard | **Ø24 mm** | Covers the body, glass envelope and the square pin-1 pad with at least 0.25 mm clearance. |
| Numbering in top/component view | Gap down; pin 1 lower right; numbers increase counterclockwise; pin 9 lower left | Provisional orientation, to be checked against the physical socket. |

At the drawing's maximum 2.1 mm terminal width and the assumed 0.5 mm thickness, the rectangular cross-section has a **2.159 mm diagonal**. A 2.5 mm circular hole leaves about **0.341 mm diametral clearance** before hole tolerances and terminal-position error. This is a fit estimate, not evidence that a socket has been measured.

The editable assumptions are in [socket-footprint.json](../hardware/top-board/socket-footprint.json). [The native footprint](../hardware/top-board/libraries/Numitron.pretty/GZC9-A_B9A_Provisional.kicad_mod) is editable in KiCad; [its rendered preview](../review/GZC9-A_B9A_Provisional.svg) shows the assigned pads. The Ø12 contact circle is retained as a drawing-layer reference only. No centre hole is added: the source does not establish that the PCB needs one.

The drawing now supports the socket body envelope and axial clearance planning. The approximately 19.94 mm maximum tube glass diameter from the RCA document remains larger than the maximum socket body, so tube spacing must also accommodate the glass.

The face view supplies no pin numbers, angular dimensions, view-direction label, or bottom-view PCB hole coordinates. The side view shows splayed terminals. The assumptions above make these gaps explicit while allowing design work to proceed. The Ø12 contact circle is not being used as the PCB drilling circle.

## Before ordering boards

Check an ordered sample against the working footprint:

- The narrow terminal cross-section: the drawing gives 2 ±0.1 mm in one direction; measure the perpendicular thickness to size the finished hole or slot.
- The terminal centres where they enter the PCB, including their relation to the indexing gap. Confirm the interpretation of the side-view 18 mm span and the seating depth.
- Any molded pin-1 mark or numbering, then the contact-to-tail mapping and viewing direction. Use that mapping to orient the numbered KiCad pads.

Revise the footprint if the sample differs; a physical fit check and continuity check close these assumptions before ordering. The tube's prefix-decimal pin verification is a separate electrical check and is also deferred during provisional layout.
