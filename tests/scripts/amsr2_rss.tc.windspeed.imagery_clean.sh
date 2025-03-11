# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source ${GEOIPS_TESTDATA_DIR}/test_data_amsr2/data/RSS_amsr2_TC-wind_daily_2020_05_18_v08.1.nc \
          --reader_name amsr2_remss_winds_netcdf \
          --product_name windspeed \
          --filename_formatter tc_clean_fname \
          --output_formatter imagery_clean \
          --metadata_filename_formatter metadata_default_fname \
          --metadata_output_formatter metadata_default \
          --trackfile_parser bdeck_parser \
          --window_start_time "20200518T0730Z" \
          --window_end_time "20200518T0740Z" \
          --trackfiles ${GEOIPS_PACKAGES_DIR}/geoips/tests/sectors/tc_bdecks/bio012020.dat \
          --compare_path "${GEOIPS_PACKAGES_DIR}/geoips/tests/outputs/amsr2_rss.tc.windspeed.imagery_clean" \
          --product_spec_override '{}' \
          --output_formatter_kwargs '{}' \
          --filename_formatter_kwargs '{}' \
          --metadata_output_formatter_kwargs '{}' \
          --metadata_filename_formatter_kwargs '{}'
ss_retval=$?

exit $((ss_retval))
