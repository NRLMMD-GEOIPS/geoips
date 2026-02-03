# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/* \
             --reader_name abi_netcdf \
             --product_name Test-Visible-Logarithmic \
             --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/abi.static.<product>.imagery_clean" \
             --output_formatter imagery_clean \
             --filename_formatter geoips_fname \
             --resampled_read \
             --sector_list test_goes16_eqc_3km_terminator_20200918T1950Z
retval=$?

exit $retval
