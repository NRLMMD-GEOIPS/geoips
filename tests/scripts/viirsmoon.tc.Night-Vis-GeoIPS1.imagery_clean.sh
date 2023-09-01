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

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.

run_procflow $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210525/191200/VJ102DNB.A2021145.1912.002.2021146004551.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210525/191200/VJ102IMG.A2021145.1912.002.2021146004551.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210525/191200/VJ102MOD.A2021145.1912.002.2021146004551.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210525/191200/VJ103DNB.A2021145.1912.002.2021146002749.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210525/191200/VJ103IMG.A2021145.1912.002.2021146002749.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210525/191200/VJ103MOD.A2021145.1912.002.2021146002749.nc \
             --procflow single_source \
             --reader_name viirs_netcdf \
             --product_name Night-Vis-GeoIPS1 \
             --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/viirsmoon.tc.<product>.imagery_clean" \
             --output_formatter imagery_clean \
             --filename_formatter tc_clean_fname \
             --trackfile_parser bdeck_parser \
             --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bio022021.dat

ss_retval=$?

exit $((ss_retval))
