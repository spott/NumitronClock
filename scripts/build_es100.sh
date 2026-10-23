#!/usr/bin/env bash
# Run inside: nix develop .#firmware
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root/firmware"
for tool in cargo flip-link picotool python3; do
    command -v "$tool" >/dev/null || { echo "Missing $tool; use nix develop .#firmware" >&2; exit 1; }
done
cargo build-pico2 --locked
target_dir=${CARGO_TARGET_DIR:-target}
elf="$target_dir/thumbv8m.main-none-eabihf/release/pico2-es100"
uf2="$target_dir/pico2-es100.uf2"
# Pico 2 is RP2350 ARM secure, not RP2040. The absolute block applies the
# RP2350-E10 boot-ROM workaround implemented by Raspberry Pi's converter.
picotool uf2 convert "$elf" -t elf "$uf2" --family rp2350-arm-s --abs-block
python3 "$repo_root/scripts/check_es100_uf2.py" "$uf2"
picotool info -a "$uf2"
printf 'UF2 ready: %s\n' "$PWD/$uf2"
