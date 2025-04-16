# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
# https://www.nrlmry.navy.mil/tcdat/tc2021/WP/WP022021/txt/SCT_winds_knmi_metop-c_WP02_202104210141
geoips run single_source \
    $GEOIPS_TESTDATA_DIR/test_data_scat/data/oscat_250/oscat_20210209_022459_scasa1_23155_o_250_2202_ovw_l2.nc \
    --reader_name scat_knmi_winds_netcdf \
    --product_name windbarbs \
    --filename_formatter tc_fname \
    --output_formatter imagery_windbarbs \
    --metadata_filename_formatter metadata_default_fname \
    --metadata_output_formatter metadata_default \
    --tc_spec_template tc_web \
    --trackfile_parser bdeck_parser \
    --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bsh192021.dat \
    --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/oscat_knmi.tc.windbarbs.imagery_windbarbs" \
    --product_spec_override '{}' \
    --output_formatter_kwargs '{}' \
    --filename_formatter_kwargs '{}' \
    --metadata_output_formatter_kwargs '{}' \
    --metadata_filename_formatter_kwargs '{}'
ss_retval=$?

exit $((ss_retval))
