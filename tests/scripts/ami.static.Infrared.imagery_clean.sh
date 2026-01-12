# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/geokompsat/20231208/0300/*.nc \
             --reader_name ami_netcdf \
             --product_name Infrared \
             --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/ami.static.<product>.imagery_clean" \
             --output_formatter imagery_clean \
             --filename_formatter geoips_fname \
             --resampled_read \
             --logging_level info \
             --sector_list geokompsat_subsector
retval=$?

exit $retval
