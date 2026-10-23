# ES100 / Pico 2 reception test

Task #8's software: a reusable `no_std` async I²C driver in [`es100/`](es100/)
and an Embassy application in [`pico2-es100/`](pico2-es100/). It tests normal
full-frame WWVB reception. Tracking mode, RTC synchronization, display firmware,
and the bottom-board design are future work.

## Build and verify

From the repository root:

```sh
nix develop .#firmware --command bash scripts/check_firmware.sh
```

This runs driver tests, formatting, Clippy for both host and Pico 2, a release
build, and UF2 inspection. To build just the firmware:

```sh
nix develop .#firmware --command bash scripts/build_es100.sh
```

Outputs (ignored by Git):

- `firmware/target/pico2-es100.uf2` — copy to a Pico 2 in BOOTSEL mode.
- `firmware/target/thumbv8m.main-none-eabihf/release/pico2-es100` — ELF with debug information.

The root `flake.lock` pins Nixpkgs and rust-overlay. The **firmware** Nix shell
supplies Rust/Cargo 1.99.1, rustfmt, Clippy, the `thumbv8m.main-none-eabihf` target,
flip-link and its LLVM linker, picotool, and picocom. No global rustup installation
is required. `firmware/rust-toolchain.toml` selects the same compiler for editors.
`firmware/Cargo.lock` pins Rust dependencies. The default Nix shell still provides
the hardware design tools.

The flake exposes Apple Silicon macOS and x86-64/AArch64 Linux shells. The
repository's existing Nixpkgs pin has dropped Intel macOS support; it cannot
provide this development shell on an Intel Mac. Compilation and
`scripts/check_firmware.sh` are verified on x86-64 Linux and Apple Silicon macOS;
AArch64 Linux is evaluated only. None of this is hardware-tested.

For interactive work:

```sh
nix develop .#firmware
cd firmware
cargo test --locked -p es100
cargo build-pico2 --locked
```

Run Cargo from `firmware/` so it finds `.cargo/config.toml`. No global default
cross-compilation target is set, so driver tests run on the host. The Pico binary
has its own memory map (4-MiB flash, 512-KiB main SRAM), retained secure IMAGE_DEF,
and flip-link stack protection. The UF2 converter uses `rp2350-arm-s` and adds
Raspberry Pi's RP2350-E10 absolute-block workaround. `check_es100_uf2.py` checks
block integrity, family IDs, flash bounds, vectors, and boot metadata markers.

## Wire with power disconnected

Use a **Pico 2**, not a Pico 1 or Pico 2 W. Match carrier **signal labels**;
module and carrier connector numbering can differ.

| ES100 carrier | Pico 2 | Physical pin |
|---|---|---:|
| VDD | 3V3 | 36 |
| GND | GND | 38 (or another ground) |
| EN | GP2 | 4 |
| IRQ− | GP3 | 5 |
| SDA | GP4 / I²C0 | 6 |
| SCL | GP5 / I²C0 | 7 |

Supply **3.3 V**; do not connect ES100 VDD to VBUS/5 V. Use external SDA and SCL
pull-ups (about 4.7 kΩ to 3V3) if the carrier does not already provide them. The
firmware disables the internal I²C pull-ups. IRQ needs no external resistor: ES100
digital pins float in shutdown, and the firmware enables the RP2350's internal
pull-up (about 50 kΩ) on GP3 to hold IRQ inactive-high. An external 10 kΩ to 3V3
is optional and harmless.
Check for fitted resistors with the circuit unpowered before adding more.
No IRQ pull-down is used, including on RP2350 A2 silicon affected by E9.

Install both antennas in the 90° holder. Keep I²C dedicated to the ES100 and
avoid polling it during reception. Begin with the receiver separated from
obvious switching noise, then test at the actual clock location.

## Flash and read logs

1. Hold **BOOTSEL** while connecting the Pico 2 to your computer over USB.
2. Copy `pico2-es100.uf2` to the **RP2350** USB mass-storage volume. It reboots.
3. Open the new USB CDC serial device. On Linux it is typically `/dev/ttyACM0`;
   on macOS, `/dev/cu.usbmodem…`. Check the actual device name.

```sh
# Run locally on the machine physically connected to the Pico.
nix develop .#firmware
picocom --baud 115200 /dev/ttyACM0
```

Baud rate is nominal for USB CDC. Exit picocom with Ctrl-A then Ctrl-X. No debug
probe or `probe-rs` is needed. These flashing and serial steps require the local
USB device; the cloud build environment cannot perform the reception experiment.

The program waits three seconds for USB enumeration, starts a full-frame receive
and records monotonic microseconds immediately after the GPIO falling-edge wait.
It then waits `IRQ_STATUS_DELAY` (10 ms) before reading IRQ Status: a 2018
time-nuts report says a read right at the edge returns stale zeros. A nonzero
status acknowledges the interrupt and is read once. A zero while IRQ is still
low means nothing was acknowledged, so it waits and reads again, up to 10 reads.
The `status_reads=` field in each `irq` line shows how many were needed; if it
is regularly above 1, raise the delay. After an unsuccessful cycle, IRQ must
return high within 100 ms, or the attempt fails as `IrqStuckLow`.

After a lock it reports UTC, elapsed time, cycle count, raw registers, antenna,
DST, leap second and next-DST information. The received second belongs to
that IRQ boundary; the code does not add a minute. `edge_us` is a **software
observation** with interrupt/executor latency, not a hardware capture or calibrated
PPS. The receiver itself specifies up to ±100 ms IRQ delay (datasheet p6).

Register reads are an address write followed by a separate read transaction,
never a combined repeated-start read, which the same report says the ES100
rejects. The driver tests fail if a combined read is ever issued.

There is one 20-minute reception deadline across all cycles, plus a bounded
three-second allowance per I²C operation. Every attempt lowers EN, then waits
30 seconds before restarting. Shutdown uses EN directly so a stuck bus cannot
prevent it. A wrong device ID, I²C error, invalid frame, stuck or unexpected IRQ
counts as an error: the radio shuts down, the attempt is logged with
`result=error consecutive_errors=n/5`, and it retries after the rest period.
A lock or a reception timeout resets the count. The firmware stops and keeps
logging a diagnostic until the Pico is reset in two cases:

- five consecutive errors (persistent wiring or pull-up fault), or
- an I²C operation that hangs past three seconds, because the cancelled
  transfer may leave the I²C peripheral unusable.

The onboard LED is lit during reception, dark between attempts, and briefly
blinks every five seconds once stopped. USB logging is nonblocking and bounded;
when no terminal is reading, old/new log data may be lost as the buffer fills.
Keep a terminal attached to collect complete runs.

`NextDst::Scheduled.hour` preserves the ES100's 1–3 hour field. The datasheet
inconsistently calls this local time (p14) and UTC (p22); this bench program does
not apply a timezone interpretation. If a "scheduled" next-DST month, day or hour
fails validation, the frame is still accepted: next DST is reported as
`Unrecognized` with the raw values, so it can be compared against the real
schedule. Special next-DST values are preserved without treating invalid
month/day registers as dates.

## Bench handoff

Builds and host tests do **not** establish hardware operation. First check for
`device_id=0x10`, an inactive-high IRQ, and a plausible UTC result. Collect several
attempts at the intended desk location during day and night, rotated about 90°,
and with the usual nearby electronics operating. Copy attempts, locks and
time-to-lock into the Obsidian **ES100 Test Plan** results table. Tracking and a
WWVB/GPS decision remain separate from this software delivery.

The driver tests cover the datasheet's control bytes and status encodings,
separate address-write/read transactions (no combined reads), burst reads, acknowledgement ownership, continued receive cycles,
BCD/calendar validation, leap seconds, next-DST special and unrecognized values and I²C errors.
Hardware bring-up, physical IRQ timing, USB behavior, timeout/retry behavior on
silicon and reception quality still need the Pico 2 and receiver.

Register and timing reference: Everset [ES100 datasheet v0.97](../datasheets/es100.pdf),
archived with source URL and SHA-256 in [`datasheets/sources.json`](../datasheets/sources.json).
