#!/usr/bin/env python3
"""Check that a generated UF2 contains a bootable Pico 2 ARM-secure image."""
import argparse
import hashlib
from pathlib import Path
import struct

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("uf2", type=Path)
args = parser.parse_args()
data = args.uf2.read_bytes()


def require(condition, message):
    if not condition:
        raise SystemExit(f"Invalid Pico 2 UF2: {message}")


require(data and len(data) % 512 == 0, "length is not a positive multiple of 512")
arm = {}
counts = set()
absolute = 0
for offset in range(0, len(data), 512):
    block = data[offset:offset + 512]
    magic0, magic1, flags, address, size, number, count, family = struct.unpack_from("<8I", block)
    require((magic0, magic1) == (0x0A324655, 0x9E5D5157), "bad block magic")
    require(struct.unpack_from("<I", block, 508)[0] == 0x0AB16F30, "bad end magic")
    require(flags & 0x2000 and size == 256, "missing family flag or unexpected payload size")
    if family == 0xE48BFF57:
        require(address == 0x10FFFF00 and flags & 0x8000, "unexpected RP2350-E10 absolute block")
        absolute += 1
        continue
    require(family == 0xE48BFF59, f"wrong family 0x{family:08x}; expected RP2350 ARM Secure")
    require(0x10000000 <= address < address + size <= 0x10400000, "outside Pico 2's 4-MiB flash")
    require(number not in arm, "duplicate application block number")
    arm[number] = (address, block[32:32 + size])
    counts.add(count)
require(absolute == 1, "expected the RP2350-E10 workaround block")
require(counts == {len(arm)} and set(arm) == set(range(len(arm))), "missing application blocks")
require(arm[0][0] == 0x10000000, "vector table is not at flash base")
image = b"".join(arm[n][1] for n in range(len(arm)))
for n in range(len(arm)):
    require(arm[n][0] == 0x10000000 + n * 256, "non-contiguous application image")
stack, reset = struct.unpack_from("<2I", image)
require(0x20000000 < stack <= 0x20080000 and stack % 8 == 0, "bad initial stack pointer")
require(reset & 1 and 0x10000000 <= reset < 0x10000000 + len(image), "bad Thumb reset vector")
require(struct.pack("<I", 0xFFFFDED3) in image[:4096], "no RP2350 IMAGE_DEF start marker")
require(struct.pack("<I", 0xAB123579) in image[:4096], "no RP2350 IMAGE_DEF end marker")
print(f"Verified Pico 2 UF2: {len(arm)} application blocks, {len(data)} bytes, E10 workaround present")
print(f"SHA256 {hashlib.sha256(data).hexdigest()}  {args.uf2}")
