# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_tpw/data/fine/comp20210419.230000.nc \
          --reader_name mimic_netcdf \
          --product_name TPW-PWAT \
          --filename_formatter tc_fname \
          --metadata_filename_formatter metadata_default_fname \
          --metadata_output_formatter metadata_default \
          --output_formatter imagery_annotated \
          --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/mimic_fine.tc.TPW-PWAT.imagery_annotated" \
          --trackfile_parser bdeck_parser \
          --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bwp022021.dat
ss_retval=$?

exit $((ss_retval))
