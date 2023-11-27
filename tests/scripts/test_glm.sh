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
# run_procflow $GEOIPS_TESTDATA_DIR/test_data_glm/raw/OR_GLM-L2-LCFA_G18_s20230010000000_e20230010000200_c20230010000213.nc \
run_procflow $GEOIPS_TESTDATA_DIR/test_data_glm/raw/*.nc \
             --procflow single_source \
             --reader_name glm_netcdf \
             --product_name flash_area \
             --output_formatter shape_patches \
             --filename_formatter geoips_fname \
             --logging_level info \
             --sector_list goes_east \
             --feature_annotator glm \
             --no_presectoring \
             --minimum_coverage 0
retval=$?

exit $retval
