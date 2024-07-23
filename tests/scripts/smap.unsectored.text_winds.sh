# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.

# For reference, bdeck file with coverage is: $GEOIPS_PACKAGES_DIR/geoips/tests/sectored/bwp202021.dat
# Not used for unsectored output, but potentially for other products
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_smap/data/RSS_smap_wind_daily_2021_09_26_NRT_v01.0.nc \
             --reader_name smap_remss_winds_netcdf \
             --product_name unsectored \
             --filename_formatter text_winds_full_fname \
             --output_formatter text_winds \
             --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/smap.unsectored.text_winds"
ss_retval=$?

exit $((ss_retval))
