# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
run_procflow $GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/geokompsat/20231208/0300/*.nc \
             --procflow single_source \
             --reader_name ami_netcdf \
             --reader_kwargs '{"self_register": "LOW"}' \
             --product_name WV-Upper \
             --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/ami.WV-Upper.unprojected_image" \
             --output_formatter unprojected_image \
             --output_formatter_kwargs '{"x_size": "1000", "y_size": "1000"}' \
             --filename_formatter geoips_fname \
             --logging_level info \
             --self_register_dataset 'Full-Disk' \
             --self_register_source ami
retval=$?

exit $retval
