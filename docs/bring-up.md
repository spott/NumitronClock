# Bring-up and layout hold points

## During top-board layout

- Use the assigned **provisional GZC9-A footprint**, as authorized by the owner on 2026-09-25. It assumes 0.5 mm terminal thickness and an 18 mm pad circle, with 2.5 mm round plated holes. See [socket dimensions and assumptions](socket.md). These sample measurements are deferred until the ordering check below.
- Route the planned decimal channel to candidate pin 1. The owner has confirmed the presence of the decimal; its pin number remains a hardware check before ordering.
- Assign a verified BH1750 WSOF6I footprint without a soldered center pad. Confirm the exact MLCC order codes and biased capacitance, plus header and semiconductor lands.
- Fit the tube/glass envelopes to the 110 x 30 mm target. RCA gives a DR2000-series maximum glass diameter of 0.785 in (about 19.94 mm); do not set tube pitch from the smaller socket body alone. Choose a deliberate HH/MM gap and mounting holes after measuring the assemblies.
- Check underside driver/header clearances, 28 AWG ribbon bend and strain-relief access, and the 25-30 mm board gap. Keep the sensor aperture exposed to room light.
- Preserve the documented 16-pin connector and supply contract. **WWVB versus GPS is bottom-board work and does not block top-board layout.** Battery sizing remains V2 work.

## Before ordering boards

- Compare the socket to a 1:1 footprint printout or fit coupon: PCB-entry terminal centres, full cross-section, seating depth and contact-to-pad numbering. Change the provisional footprint if needed.
- Verify the actual decimal connection between socket common pin 2 and candidate pin 1 with a current-limited test, then record the mapping.
- Complete footprint, assembly-clearance and manufacturing-rule checks. LDO copper area and current paths are designed during layout; actual temperature, startup and brownout measurements follow on the assembled prototype.

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
