# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/* \
             --reader_name seviri_hrit \
             --product_name Convective_Storms \
             --output_formatter imagery_clean \
             --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/seviri.Convective_Storms.imagery_clean" \
             --sector_list global \
             --filename_formatter geoips_fname
retval=$?

exit $retval
