#!/usr/bin/env bash
# Run from the repo root: nix develop .#firmware --command bash scripts/check_firmware.sh
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root/firmware"
cargo fmt --all -- --check
cargo test --locked -p es100
cargo clippy --locked -p es100 --all-targets -- -D warnings
cargo clippy --locked -p pico2-es100 --release --target thumbv8m.main-none-eabihf -- -D warnings
bash "$repo_root/scripts/build_es100.sh"
