# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
test_sector_name=$1
shift
reader_name=$1
shift
product_name=$1
shift
repo_name=$1
shift
files=$@

# test_sector_name=test_goes16_eqc_3km_edge_day_20200918T1950Z
# reader_name=abi_netcdf
# product_name="Infrared-Day-Only"
# files="$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/*"

geoips run single_source $files \
             --reader_name $reader_name \
             --reader_kwargs '{"satellite_zenith_angle_cutoff": None}' \
             --product_name $product_name \
             --compare_path "$GEOIPS_PACKAGES_DIR/${repo_name}/tests/integration_tests/tiny_sectors/outputs/${test_sector_name}_${product_name}" \
             --output_formatter imagery_clean\
             --filename_formatter geoips_fname \
             --minimum_coverage 0 \
             --resampled_read \
             --sector_list $test_sector_name
retval=$?

exit $retval
