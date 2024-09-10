# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/himawari8/20200405/0000/* \
          --reader_name ahi_hsd \
          --product_name WV \
          --filename_formatter geotiff_fname \
          --output_formatter geotiff_standard \
          --trackfile_parser bdeck_parser \
          --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bsh252020.dat \
          --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/ahi.tc.<product>.geotiff" \
          --logging_level debug \
          --resampled_read
retval=$?

exit $retval
