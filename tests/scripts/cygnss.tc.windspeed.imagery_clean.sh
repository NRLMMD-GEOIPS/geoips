# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

geoips run single_source \
    $GEOIPS_TESTDATA_DIR/test_data_cygnss/data/cyg.ddmi.s20240125-000001-e20240125-235959.l2.wind_trackgridsize25km_NOAAv1.2_L1a21.d21.nc \
    --reader_name cygnss_netcdf \
    --product_name windspeed \
    --output_formatter imagery_clean \
    --filename_formatter tc_clean_fname \
    --window_start_time "20240125T0600Z" \
    --window_end_time "20240125T0615Z" \
    --minimum_coverage 0 \
    --trackfile_parser bdeck_parser \
    --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bsh062024.dat \
    --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/cygnss.tc.windspeed.imagery_clean" \

ss_retval=$?

exit $((ss_retval))