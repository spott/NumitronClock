# Numitron Clock

- Prefer the pinned Nix flake for project tooling. Do not make global package installs.
- The top-board milestone is schematic capture and review. Do not turn unmeasured socket geometry into fabrication-ready PCB files.
- Keep relevant manufacturer datasheets in `datasheets/` and include them in Git commits; retain source URLs and SHA-256 hashes in the index.
- Owner confirms DR2000-marked tubes with visible prefix decimal points. The archived RCA table differs: preserve that observation and verify the decimal pin on actual hardware.
- Native KiCad files in `hardware/top-board/` are the editable design. `scripts/build_schematic.py --write` overwrites them; use it only before subsequent manual CAD edits or after reconciling those edits.
- Run `nix develop --command bash scripts/review.sh` after electrical changes, then visually inspect the rendered sheets. ERC alone is not a hardware or footprint qualification.
- Bottom-board implementation, radio selection, and final PCB layout are separate milestones.
