# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_mtg_fci_day/data/mt1_fdhsi_20240113_1150/* \
             --reader_name fci_netcdf \
             --product_name Visible \
             --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/fci.static.<product>.imagery_annotated" \
             --output_formatter imagery_annotated \
             --filename_formatter geoips_fname \
             --sector_list global

retval=$?

exit $retval
