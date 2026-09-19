# Top-board electrical design

Revision 0.1 follows the Obsidian plan's detailed top-board decisions: four tubes, static TPIC6B595 sinks, AHCT level conversion, BH1750 ambient light, AP7361C linear tube supply, and a flexible 16-way interface. V1 is USB-powered; there is no battery circuitry on this board.

## Power and driver checks

U1 is the selected **AP7361C-Y5-13**, LCSC C507885 as recorded in the plan. Its SOT89-5 pinout is **1 EN, 2 GND/tab, 3 ADJ, 4 IN, 5 OUT**. It is not interchangeable with similarly named fixed-voltage or SOT223 symbols. The project-local symbol was captured from [Diodes' datasheet](../datasheets/AP7361C.pdf), pp. 1-2.

R1=46.4k and R2=10k set `0.8*(1+46.4/10) = 4.512 V` nominal, before reference/resistor tolerance and ADJ leakage. Both resistors are 1%; this is an approximate 4.5 V supply. No driver-drop compensation is applied. C1 is the input reservoir; C2 and C3 give 20 uF nominal output capacitance. Final capacitor order codes must retain at least 2.2 uF effective total after DC bias, tolerance and temperature. Route the feedback divider away from switched filament current and return it to the regulator ground.

Four tubes times eight channels times the plan's nominal 24 mA gives **0.768 A** as a conservative steady full-test-pattern estimate. This is not a cold-start bound or a prediction of average PWM power. At that current:

| LDO input | Nominal output | Estimated LDO heat | Rise using datasheet's 150 C/W SOT89-5 example |
|---:|---:|---:|---:|
| 5.00 V | 4.512 V | 0.375 W | 56 C |
| 5.25 V | 4.512 V | 0.567 W | 85 C |

These are calculations, not measured temperatures or qualified thermal limits. The datasheet's copper/board conditions differ from the final board. Allocate a substantial grounded copper area around the SOT89 tab, check both sides of the PCB and enclosure airflow, then measure at full pattern and actual useful brightness. The chosen package remains the planned part; if it fails the thermal check, revisit its package rather than claiming PWM makes it safe.

There is only about 0.49 V nominal headroom from a 5 V input. USB, protection circuitry, connector and ribbon losses can make the LDO drop out. Its tabulated dropout data is not a guarantee of a regulated 4.512 V output at every allowed USB voltage and display current. Confirm minimum input voltage at J1 and actual V_TUBE under load. The TPIC/AHCT logic rail must also remain in their 4.5-5.5 V operating range.

The TPIC6B595 is a **voltage-switched sink, not a constant-current driver**. The original plan's approximate 1-ohm drain resistance is optimistic: [TI's datasheet](../datasheets/tpic6b595.pdf), p. 5, gives 4.2 ohms typical and 5.7 ohms maximum at its stated 100 mA / 4.5 V / room-temperature test conditions. Using 4.2 ohms as a rough estimate at 24 mA gives about 0.10 V drop and 2.4 mW per segment. Verify actual filament voltage/current; incandescent resistance changes with temperature.

## Pinout and startup details

- TPIC **SRCK is pin 13**, checked against its package diagram and application circuit. The Rev. D p. 3 pin-function table erroneously says 15, which is also listed as DRAIN5. All three ground pins (10, 11, 19) are connected; NC pins 1 and 20 have no-connect markers.
- U2 is a 5 V **SN74AHCT125DR**, not HC125. [TI's AHCT datasheet](../datasheets/sn74ahct125.pdf) specifies TTL input thresholds suitable for the 3.3 V controls. R3-R6 are 33-ohm source-series damping resistors; check their usefulness with the real placement and edges.
- Q1 and DISPLAY_ARM add an explicit disarmed state. No 5 V pull-up reaches a bottom-board GPIO. Buffer output defaults are independent of an absent 3.3 V rail.
- R15=1k pulls up the four shared AHCT enable inputs; R16=2.2k supplies Q1's base current. The stronger enable pull-up limits the rise time at this capacitive node. Keep this net short and check the AHCT input-transition requirement on the assembled board.
- R11-R13 and R17 are 4.7k pull-downs. This also accommodates RP2350 **A2** erratum E9, whose workaround calls for 8.2k or lower external pull-downs. E9 is fixed in A3; keeping the stronger pull-downs supports either revision. See the archived [RP2350 datasheet](../datasheets/rp2350-datasheet.pdf), Appendix E, RP2350-E9.
- No claim of power-on register contents is made: firmware must blank, shift zeros and latch before showing a frame. The normal reset/disconnection state is addressed; marginal supply ramps and brownout still require a scope check.

## Light sensor

The [ROHM BH1750FVI datasheet](../datasheets/bh1750fvi.pdf), pp. 6-9 and 13, requires DVI low after VCC becomes valid. A simple RC alone has supply-ramp and rapid-restart conditions. U4, **TLV809EA29DBZR**, instead provides a defined reset from the 3.3 V rail. Its normal DBZ pinout is 1 GND, 2 RESET_N, 3 VDD; the R/V alternate pinout variants are not substitutes. R18=1k and C6=100n add a small release filter. [TI supervisor datasheet](../datasheets/tlv809e.pdf), pp. 4-5 and 9.

The sensor is on 3.3 V with local bypassing and address 0x23. R19=10k holds ADDR low, allowing for the specified input leakage. Its **exposed central metal is not to be soldered or electrically connected** (ROHM p. 16). Do not choose an ordinary exposed-pad six-pin footprint by package size alone. Obtain/verify the WSOF6I recommended lands before assigning its footprint. Place the optical aperture on the tube side with a view of room light and away from direct filament illumination; reserve space for a small shield if required.

## Tube identity and socket

The [RCA document](../datasheets/dr2000.pdf), PDF pp. 3-4, maps segments A-G to socket pins 7,8,5,4,3,9,6, with common on pin 2. It lists DR2000 pin 1 as NC and DR2010 pin 1 as a prefix decimal. **The owner explicitly reports DR2000 markings and visible prefix decimals.** That observation is retained as the project requirement. All eight channels are routed, with pin 1's decimal assignment marked provisional until the actual tubes are checked. It is not treated as a reason to change the display to a colon or discard the planned separator.

Socket order link: [Amazon listing B0BGBJ7L41](https://www.amazon.com/dp/B0BGBJ7L41), supplied as `https://a.co/d/02oJ9ki1`. The short link resolved, but the listing and its dimension image could not be retrieved in this session. No unverified drawing from a different seller was substituted. The Obsidian dimensions (approximately 12 mm contact circle, 18 mm body and 9 mm body height) are planning inputs, **not a PCB drill pattern**.

The stock KiCad footprints assigned to the other parts exist in KiCad 10.0.5. That availability check is not a production land-pattern audit. In particular, compare the header's 1.1 mm recommended drill, SOT89 tab geometry and connector height against the chosen parts before layout release.
