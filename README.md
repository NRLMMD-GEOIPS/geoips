    # # # Distribution Statement A. Approved for public release. Distribution unlimited.
    # # #
    # # # Author:
    # # # Naval Research Laboratory, Marine Meteorology Division
    # # #
    # # # This program is free software: you can redistribute it and/or modify it under
    # # # the terms of the NRLMMD License included with this program. This program is
    # # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
    # # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
    # # # for more details. If you did not receive the license, for more information see:
    # # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

# GitHub Pages Deployment Branch

This branch hosts the deployed documentation for the GeoIPS package, for both released versions and `dev` (the current `main` branch), which is made available at [nrlmmd-geoips.github.io/geoips/](https://nrlmmd-geoips.github.io/geoips/).

Other than initial configuration, this branch should not need to be interacted with directly, but instead via GitHub Actions. Key features of this branch (which primarily are there to enable the version switching functionality of the `sphinx-pydata-theme`) include:
- the `versions.json` file, which must exist at a static location, so that the PyData theme (in each deployed version) can point to it to drive the version switcher.
- `index.html`, which is a simple HTML meta redirect to the latest docs
- the `stable` symlink, which links to whichever directory corresponds to the latest stable version (and typically ought not point to the `dev` directory)
