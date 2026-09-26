# Inter-board interface, revision 0.1

J1 is a keyed, shrouded 2x8 male PCB header: **Wurth 61201621621**. Cable sockets: **61201623021**, specified with strain relief. Cable: 16-conductor, 28 AWG, 1.27 mm pitch ribbon; 3M 3365/16 is a documented candidate. Start with about 150 mm of ribbon, then choose the length after checking the debugging and enclosure folds.

The **PCB pin grid is 2.54 mm**, while the **ribbon conductor pitch is 1.27 mm**. These are intentionally different.

## Numbering and orientation

This is the **male header's mating-face view**, looking into its shroud with the key notch at the bottom, as in the archived Wurth drawing. It is not a PCB solder-side view or the female cable connector's mating-face view.

```text
             male header mating face
       +---------------------------------+
       |  2   4   6   8  10  12  14  16 |
       |  1   3   5   7   9  11  13  15 |
       +--------------     --------------+
                     key notch
          ^
       pin 1 / marked ribbon conductor
```

Revision 0.2 placement: J1 is on the **underside**, with its long axis **front to rear**, perpendicular to the tube row. Its body centre is (55, 14.9) mm relative to the board's upper-left in the top view. In that view pin 1 is at (56.27, 6.01) mm and pin 2 at (53.73, 6.01) mm; subsequent rows advance 2.54 mm toward the front. The key notch points toward +X in the top view (toward the minute tubes), and toward the left in the mirrored underside view. The male mating-face numbering above and electrical assignment are unchanged. This orientation creates space between the two tube pairs; confirm cable access and strain-relief clearance in the enclosure. The board includes a pin-1 mark, connector revision and labelled supply test points.

The cable is **straight through: pin n to pin n**, including all six grounds and both 5 V conductors. Confirm the finished assembly with a continuity meter; do not infer numbering from a photograph of the opposite mating face. Power down before separating or reconnecting the boards.

## Electrical assignment

Directions are relative to the top board. All logic at J1 is 3.3 V.

| Pin | Net | Direction | Purpose / reset state |
|---:|---|---|---|
| 1 | GND | Return | Ground |
| 2 | SER_3V3 | In | Serial data; 4.7k pull-down |
| 3 | GND | Return | Ground beside serial/clock |
| 4 | SRCK_3V3 | In | Shift clock; 4.7k pull-down |
| 5 | GND | Return | Ground beside clocks |
| 6 | RCK_3V3 | In | Storage-register latch; 4.7k pull-down |
| 7 | GND | Return | Ground beside latch/blank |
| 8 | BLANK_3V3 | In | **High = dark**, low = outputs enabled; 4.7k pull-up to 3.3 V |
| 9 | +3V3 | Power in | BH1750 and reset supervisor |
| 10 | SDA | Bidirectional | I2C, 3.3 V pull-ups on bottom board |
| 11 | GND | Return | Ground between SDA/SCL |
| 12 | SCL | In | I2C clock |
| 13 | DISPLAY_ARM | In | High enables the level shifter; 4.7k pull-down |
| 14 | +5V | Power in | Parallel supply conductor A |
| 15 | GND | Return | Supply return |
| 16 | +5V | Power in | Parallel supply conductor B |

`DISPLAY_ARM` uses the otherwise spare conductor. Through R16 and Q1 it pulls the four AHCT enable pins low. When disarmed, all four buffers become high impedance, R7-R9 hold data/clocks low, and R10 holds the TPIC output-disable line high. This also leaves the display dark when the MCU is disconnected or its pins are in their reset state. It is not a full undervoltage supervisor for the 5 V rail; test brownout behavior during bring-up.

Allow approximately 2 mA of GPIO source current for DISPLAY_ARM high, including its pull-down and Q1 base current. Configure at least 4 mA output drive strength on the RP2350.

The +5V and +3V3 pins are **inputs** to the top board. The 4.512 V nominal filament rail is generated locally and does not cross the ribbon. The bottom-board interface must not backfeed an unpowered top board. Supply both rails before driving the interface.

## Display protocol

- Initial SPI setting: mode 0, MSB first, 100 kHz. Verify real cable edges before increasing the clock rate. Keep RCK low during shifting, pulse it only after the 32 bits have been sent and SRCK is low.
- Cascade: U5 (hours tens) -> U6 (hours units) -> U7 (minutes tens) -> U8 (minutes units).
- Send bytes in order **`[minutes_units, minutes_tens, hours_units, hours_tens]`**.
- A `1` lights a segment. Bits 0..6 are A..G. Bit 7 drives socket pin 1, the provisional decimal connection.
- Set bit 7 only for V3, the minutes-tens tube, to make the HH.MM separator after the pin has been verified. Keep the other decimals off.
- TP5 is U8's **5 V** serial output for a logic probe. It is not connected back to an MCU input.

| Segment | Bit | TPIC drain | TPIC pin | Tube socket pin |
|---|---:|---:|---:|---:|
| A, top | 0 | 0 | 4 | 7 |
| B, upper right | 1 | 1 | 5 | 8 |
| C, lower right | 2 | 2 | 6 | 5 |
| D, bottom | 3 | 3 | 7 | 4 |
| E, lower left | 4 | 4 | 14 | 3 |
| F, upper left | 5 | 5 | 15 | 9 |
| G, center | 6 | 6 | 16 | 6 |
| Prefix decimal, verify | 7 | 7 | 17 | 1 |
| Common | - | - | - | 2, connected to V_TUBE |

Suggested seven-segment glyph bytes: `0=0x3f, 1=0x06, 2=0x5b, 3=0x4f, 4=0x66, 5=0x6d, 6=0x7d, 7=0x07, 8=0x7f, 9=0x6f, blank=0x00`. Add `0x80` only when the verified decimal is required.

Startup: hold ARM low; configure data/clocks low and BLANK high; raise ARM while BLANK remains high; shift/latch 32 zero bits; load the intended frame; then start brightness PWM. **Lit duty is the fraction of time BLANK is low**, so invert a peripheral's high-duty setting if necessary. SRCLR is tied high locally; latching zero data clears the displayed state.

## Ambient light

U3 uses 7-bit address **0x23**. R19 pulls ADDR low. U4 supervises 3.3 V and holds DVI low during reset; R18/C6 filter the release. Wait at least **300 ms after stable 3.3 V** before initializing the sensor (the chosen supervisor's specified release delay is 130-270 ms). Keep SDA/SCL released until then; begin at 100 kHz I2C.

R20/R21 are **DNP by default**. The bottom board owns the shared bus pull-ups; fit the top-board pair only for a standalone test or if the bottom pair is absent. Check bus rise time with the assembled ribbon before selecting 400 kHz or changing pull-up values.
