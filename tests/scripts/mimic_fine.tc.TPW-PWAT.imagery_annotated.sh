# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
run_procflow $GEOIPS_TESTDATA_DIR/test_data_tpw/data/fine/comp20210419.230000.nc \
          --procflow single_source \
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
