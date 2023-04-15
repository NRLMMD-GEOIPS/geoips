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
run_procflow $GEOIPS_TESTDATA_DIR/test_data_gpm/data/3B-HHR-L.MS.MRG.3IMERG.20200917-S170000-E172959.1020.V06B.RT-H5 \
          --procflow single_source \
          --reader_name imerg_hdf5 \
          --product_name Rain \
          --filename_formatter tc_fname \
          --output_formatter imagery_clean \
          --trackfile_parser bdeck_parser \
          --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bal202020.dat \
          --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/imerg.tc.Rain.imagery_clean"
ss_retval=$?

exit $((ss_retval))
