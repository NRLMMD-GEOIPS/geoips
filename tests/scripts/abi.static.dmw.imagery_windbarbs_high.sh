# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/goes16/20210929/0000/OR_ABI-L2-DMWVF*.nc \
             --reader_name abi_l2_netcdf \
             --product_name DMW-High \
             --output_formatter imagery_windbarbs \
             --filename_formatter geoips_fname \
             --resampled_read \
             --logging_level info \
             --sector_list goes_east \
             --minimum_coverage 0 \
             --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/abi.static.<product>.imagery_windbarbs" \

retval=$?

exit $retval
