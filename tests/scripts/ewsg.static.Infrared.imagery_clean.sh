# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_ewsg/data/2020.1211.2312.goes-13.gvar.nc \
          --reader_name ewsg_netcdf \
          --product_name Infrared \
          --filename_formatter geoips_fname \
          --output_formatter imagery_clean \
          --sector_list ewsg \
          --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/ewsg.static.<product>.imagery_clean"
retval=$?

exit $retval
