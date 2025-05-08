# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/goes16/20200918/1950/* \
    --reader_name abi_netcdf \
    --product_name Infrared \
    --output_formatter imagery_annotated \
    --filename_formatter geoips_fname \
    --logging_level info \
    --resampled_read \
    --feature_annotator default_oldlace \
    --gridline_annotator default_palegreen \
    --sector_list goes_east
retval=$?

exit $retval


            #  --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/abi.static.<product>.imagery_annotated_enhanced" \
