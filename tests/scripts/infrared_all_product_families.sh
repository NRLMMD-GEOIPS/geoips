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
run_procflow $GEOIPS_TESTDATA_DIR/test_data_smap/data/RSS_smap_wind_daily_2021_09_26_NRT_v01.0.nc \
             --procflow single_source \
             --reader_name smap_remss_winds_netcdf \
             --product_name xdict_out_form \
             --output_formatter text_winds \
             --filename_formatter text_winds_full_fname \
             --sector_list goes_east
retval=$?

exit $retval

# --reader_name abi_netcdf
# --output_formatter imagery_annotated
# --filename_formatter geoips_fname
# --resampled_read
# --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/abi.static.<product>.imagery_annotated" \
# run_procflow $GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/goes16/20200918/1950/* \
