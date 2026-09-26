{
  description = "Numitron clock hardware design and verification tools";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "aarch64-darwin" "x86_64-darwin" "aarch64-linux" "x86_64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in {
      devShells = forAllSystems (system:
        let pkgs = import nixpkgs { inherit system; };
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
        });
    };
}
