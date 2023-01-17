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

#!/bin/bash

out_path=$GEOIPS_PACKAGES_DIR/geoips/tests/outputs

# Ensure netcdf output files are gunzipped
    date -u
    if ls $out_path/*/*.gz >& /dev/null; then
        echo "gunzip output files $out_path/*/*.gz"
        gunzip -f $out_path/*/*.gz
    fi
