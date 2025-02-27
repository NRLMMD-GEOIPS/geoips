# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_tpw/data/coarse/comp20210723.000000.nc \
          --reader_name mimic_netcdf \
          --product_name TPW-CIMSS \
          --filename_formatter geoips_fname \
          --output_formatter imagery_annotated \
          --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/mimic_coarse.static.TPW-CIMSS.imagery_annotated" \
          --sector_list global_cylindrical
ss_retval=$?

exit $((ss_retval))
