# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_gpm/data/3B-HHR-E.MS.MRG.3IMERG.20251028-S193000-E195959.1170.V07B.RT-H5 \
          --reader_name imerg_hdf5 \
          --product_name Rain \
          --filename_formatter tc_fname \
          --output_formatter imagery_clean \
          --trackfile_parser bdeck_parser \
          --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bal132025.dat \
          --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/imerg.tc.Rain.imagery_clean"
ss_retval=$?

exit $((ss_retval))
