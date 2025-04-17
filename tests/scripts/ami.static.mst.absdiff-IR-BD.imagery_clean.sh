# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_multi_scan_times/data/geokompsat-ami/LA/*ir112*.nc \
    --reader_name ami_netcdf \
    --product_name absdiff-IR-BD \
    --output_formatter imagery_clean \
    --filename_formatter geoips_fname \
    --logging_level info \
    --minimum_coverage 0 \
    --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/ami.static.mst.<product>.imagery_clean" \
    --sector_list geokompsat_subsector
retval=$?

exit $retval
