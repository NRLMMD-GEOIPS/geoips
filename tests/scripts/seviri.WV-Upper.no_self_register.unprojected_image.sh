# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20250624/1200/H-000-MSG3* \
    --reader_name seviri_hrit \
    --product_name WV-Upper-No-SR \
    --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/seviri.WV-Upper.no_self_register.unprojected_image" \
    --output_formatter unprojected_image \
    --output_formatter_kwargs '{"x_size": "1000", "y_size": "1000"}' \
    --filename_formatter basic_fname
retval=$?

exit $retval
