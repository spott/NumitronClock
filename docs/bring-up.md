# Bring-up and layout hold points

## Completed layout basis

The revision 0.2 top PCB uses a 110 × 40 mm working outline, all 55 schematic components, four proposed M2.5 mounting positions, two copper layers and front/back ground pours. It includes the manufacturer-based U1 and J1 lands and six-land BH1750 pattern with an unsoldered centre. The authorized [provisional socket geometry](socket.md) and candidate pin-1 decimal connection are retained. [Layout notes](placement.md) record coordinates, assumptions and tool checks.

## Before ordering boards

- Compare the socket to a 1:1 footprint printout or fit coupon: PCB-entry terminal centres, full cross-section, seating depth and contact-to-pad numbering. Change the provisional footprint if needed.
- Verify the actual decimal connection between socket common pin 2 and candidate pin 1 with a current-limited test, then record the mapping.
- Confirm that the 110 × 40 mm working outline, perpendicular underside connector, ribbon strain relief/bend and proposed M2.5 hardware fit the enclosure and 25–30 mm board spacing. The original 30 mm depth was increased to fit the driver strip.
- Freeze exact capacitor order codes and verify effective capacitance at operating voltage; C2+C3 must retain at least 2.2 uF total. Inspect the WSOF6I lead/land correspondence, solder-mask openings, stencil and ordered component packages.
- Review the current ERC/DRC and plots against the chosen fabricator's rules. The layout includes regulator heat-spreading copper and thermal vias; measure actual temperature, startup and brownout on the prototype.

## Bench sequence

1. **Unpowered:** inspect assembly, pin 1 marks and regulator orientation. Check resistance between all supply rails and ground, both 5 V pins, all ground pins, socket commons and segment nets. Verify straight-through cable numbering with a meter.
2. **No tubes installed:** use a current-limited bench supply, confirm +5V, +3V3 and V_TUBE at TP1-TP4. Check regulator output before exposing the tubes. Confirm the bottom board supplies the two independent input rails as specified.
3. **Default-off behavior:** with the controller disconnected and again with it held in reset, scope BLANK_5V high and confirm the drivers remain disabled. Exercise slow supply rise, rapid restart, single-rail conditions and brownout. This is verification of the circuit's intended behavior, not a hot-plug qualification.
4. **Logic:** keep BLANK high; assert ARM; clock/latch zeros; shift a walking-one pattern and inspect SER, SRCK, RCK and TP5. Verify the rightmost byte reaches U8 and all latch edges occur with SRCK low. Begin at 100 kHz; inspect ringing before changing rate.
5. **One tube:** start with short, low-duty single-segment pulses and an appropriate supply current limit. Confirm A-G and common before testing the decimal. Do not use a supply overshoot or higher rail voltage to force brightness. Record the tube marking and confirmed pin-1 behavior.
6. **Four tubes:** load known glyphs and the V3 separator. Check for unwanted flashes on resets and frame updates. Measure startup/inrush, peak rail current, +5V at J1, V_TUBE, ground drop and representative segment voltage. A nominal 0.77 A steady estimate does not bound cold-filament current.
7. **Ambient light:** after at least 300 ms of stable 3.3 V, initialize/read address 0x23. Verify DVI reset on rapid repowering. Check rise time with the actual shared I2C pull-ups. Compare covered/exposed readings and ensure filament glow does not drive a dimming feedback loop.
8. **Thermal and brightness:** test the full pattern and normal time display at nominal/high input voltage, then at comfortable day/night settings inside the enclosure. Record LDO case temperature, ambient temperature, current, power, PWM duty and lux. These measurements feed the bottom-board telemetry and eventual V2 battery decisions.

## Release evidence to record

Keep measured socket drawings, verified tube mapping, connector continuity, oscilloscope captures, regulator/load/temperature measurements, capacitor selection, and the final ERC/DRC reports in the repository. This board has not been assembled or measured; its passing automated checks do not close these hold points.
