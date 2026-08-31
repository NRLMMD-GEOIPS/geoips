{
  description =
    "GeoIPS - Geolocated Information Processing System. Jointly developed and maintained by the Naval Research Laboratory (NRL) Marine Meteorology Division and the Cooperative Institute for Research in the Atmosphere (CIRA) at Colorado State University.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python312;

        # Native libraries the GeoIPS scientific stack links against
        # (cartopy/pyproj -> proj+geos, netCDF4/h5py -> hdf5+netcdf,
        # pygrib -> eccodes, pyhdf -> hdf4, numpy/scipy -> openblas).
        nativeLibs = with pkgs; [
          geos
          proj
          hdf5
          netcdf
          hdf4
          eccodes
          openblas
          zlib
        ];
      in {
        devShells.default = pkgs.mkShell {
          venvDir = "./.venv";

          packages = nativeLibs ++ (with pkgs; [ pkg-config gcc gfortran ]);

          buildInputs = [
            python
            python.pkgs.venvShellHook
            python.pkgs.pip
          ];

          # venvShellHook creates ./.venv on first entry and runs this once;
          # GeoIPS 2.0a and its dependencies are installed from the checkout.
          postVenvCreation = ''
            python -m pip install --upgrade pip
            python -m pip install -e .
          '';

          postShellHook = ''
            export PROJ_DIR=${pkgs.proj}
            export GEOS_DIR=${pkgs.geos}
            export HDF5_DIR=${pkgs.hdf5}
            export ECCODES_DIR=${pkgs.eccodes}
            export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath nativeLibs}:$LD_LIBRARY_PATH
            echo "GeoIPS dev shell ready - run 'geoips --help' to get started."
          '';
        };

        formatter = pkgs.nixpkgs-fmt;
      });
}
