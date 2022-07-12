# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # # 
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # # 
# # # This program is free software:
# # # you can redistribute it and/or modify it under the terms
# # # of the NRLMMD License included with this program.
# # # 
# # # If you did not receive the license, see
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/
# # # for more information.
# # # 
# # # This program is distributed WITHOUT ANY WARRANTY;
# # # without even the implied warranty of MERCHANTABILITY
# # # or FITNESS FOR A PARTICULAR PURPOSE.
# # # See the included license for more details.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.

# For reference, bdeck file with coverage is: $GEOIPS/tests/sectored/bwp202021.dat
# Not used for unsectored output, but potentially for other products
run_procflow ${GEOIPS_BASEDIR}/test_data/test_data_smap/data/RSS_smap_wind_daily_2021_09_26_NRT_v01.0.nc \
             --procflow single_source \
             --reader_name smap_remss_winds_netcdf \
             --product_name unsectored \
             --filename_format text_winds_full_fname \
             --output_format text_winds \
             --compare_path "$GEOIPS/tests/outputs/smap.unsectored.text_winds"
ss_retval=$?

exit $((ss_retval))
