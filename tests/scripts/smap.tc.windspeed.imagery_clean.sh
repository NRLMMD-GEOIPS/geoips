# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Note this includes test of --window_start_time and --window_end_time

geoips run single_source \
    $GEOIPS_TESTDATA_DIR/test_data_smap/data/RSS_smap_wind_daily_2021_09_26_NRT_v01.0.nc \
    --reader_name smap_remss_winds_netcdf \
    --product_name windspeed \
    --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/smap.tc.windspeed.imagery_clean" \
    --output_formatter imagery_clean \
    --filename_formatter tc_clean_fname \
    --window_start_time "20210926T2000Z" \
    --window_end_time "20210926T2200Z" \
    --trackfile_parser bdeck_parser \
    --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bwp202021.dat
ss_retval=$?

exit $((ss_retval))
