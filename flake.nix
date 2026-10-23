{
  description = "Numitron clock hardware and embedded Rust tools";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  inputs.rust-overlay.url = "github:oxalica/rust-overlay";
  inputs.rust-overlay.inputs.nixpkgs.follows = "nixpkgs";

  outputs = { self, nixpkgs, rust-overlay }:
    let
      # The existing Nixpkgs pin has dropped x86_64-darwin support.
      systems = [ "aarch64-darwin" "aarch64-linux" "x86_64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in {
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs {
            inherit system;
            overlays = [ rust-overlay.overlays.default ];
          };
          rustToolchain = pkgs.rust-bin.fromRustupToolchainFile ./firmware/rust-toolchain.toml;
        in {
          default = pkgs.mkShellNoCC {
            packages = [
              (pkgs.python3.withPackages (p: [ p.sexpdata p.pypdf ]))
              pkgs.poppler-utils
              pkgs.librsvg
              pkgs.freerouting
            ];
            # Use the existing KiCad installation on macOS. No global installs.
            shellHook = ''
              export FONTCONFIG_FILE="${pkgs.fontconfig.out}/etc/fonts/fonts.conf"
              if [ -d /Applications/KiCad/KiCad.app/Contents/MacOS ]; then
                export PATH="/Applications/KiCad/KiCad.app/Contents/MacOS:$PATH"
              fi
            '';
          };
          firmware = pkgs.mkShell {
            packages = [ rustToolchain pkgs.flip-link pkgs.picotool pkgs.picocom pkgs.python3 pkgs.git ];
            FLIP_LINK_LD = "${rustToolchain}/lib/rustlib/${pkgs.stdenv.hostPlatform.rust.rustcTarget}/bin/rust-lld";
          };
        });
    };
}
