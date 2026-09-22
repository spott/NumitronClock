# Bring-up and layout hold points

## Before PCB layout

- The **GZC9-A drawing is archived**; see [socket dimensions and remaining checks](socket.md). Confirm the PCB-entry terminal centres, the metal thickness missing from the 2 ±0.1 mm width callout, seating depth and pin-number mapping on an ordered sample. Use those to set holes/slots and annular rings. The Ø12 contact circle and side-view terminal span are distinct dimensions.
- Verify the actual decimal connection between socket common pin 2 and candidate pin 1 with a current-limited test, then record the mapping. The owner has confirmed the presence of the decimal; its pin number still needs confirmation.
- Assign a verified BH1750 WSOF6I footprint without a soldered center pad. Confirm the exact MLCC order codes and biased capacitance, plus header and semiconductor lands.
- Fit the tube/glass envelopes to the 110 x 30 mm target. RCA gives a DR2000-series maximum glass diameter of 0.785 in (about 19.94 mm); do not set tube pitch from the smaller socket body alone. Choose a deliberate HH/MM gap and mounting holes after measuring the assemblies.
- Check underside driver/header clearances, 28 AWG ribbon bend and strain-relief access, and the 25-30 mm board gap. Keep the sensor aperture exposed to room light.
- Resolve the plan's time-source decision before board layout, and agree the bottom-board interface and available supply current. Battery sizing remains V2 work.

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

Keep measured socket drawings, verified tube mapping, connector continuity, oscilloscope captures, regulator/load/temperature measurements, capacitor selection, and the final ERC/DRC reports in the repository. This schematic has not been assembled or measured; its passing automated checks do not close these hold points.
