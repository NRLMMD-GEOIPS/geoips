# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.

run_procflow \
    $GEOIPS_TESTDATA_DIR/test_data_arctic_weather_satellite/data/20250428/W_NO-KSAT-Tromso%2CSAT%2CAWS1-MWR-1B-RAD_C_OHB__20250428133939*.nc \
    --procflow single_source \
    --reader_name aws_netcdf \
    --product_name TB325-1 \
    --filename_formatter tc_clean_fname  \
    --output_formatter imagery_clean \
    --tc_spec_template tc_web \
    --trackfile_parser bdeck_parser \
    --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bwp992025.dat \
    --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/aws.tc.<product>.imagery_clean" \
    --product_spec_override '{}' \
    --output_formatter_kwargs '{}' \
    --filename_formatter_kwargs '{}' \
    --metadata_output_formatter_kwargs '{}' \
    --metadata_filename_formatter_kwargs '{}'
ss_retval=$?

exit $((ss_retval))
