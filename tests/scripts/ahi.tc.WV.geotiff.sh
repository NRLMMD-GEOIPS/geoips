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
run_procflow $GEOIPS_BASEDIR/test_data/test_data_ahi_day/data/20200405_0000/* \
          --procflow single_source \
          --reader_name ahi_hsd \
          --product_name WV \
          --filename_format geotiff_fname \
          --output_format geotiff_standard \
          --trackfile_parser bdeck_parser \
          --trackfiles $GEOIPS/tests/sectors/tc_bdecks/bsh252020.dat \
          --compare_path "$GEOIPS/tests/outputs/ahi.tc.<product>.geotiff" \
          --resampled_read
retval=$?

exit $retval
