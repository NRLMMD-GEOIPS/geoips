# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

run_procflow $GEOIPS_TESTDATA_DIR/test_data_sgli/data/20251018T0233/*DL*.h5 \
    --procflow single_source \
    --log info \
    --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/sgli.static.<product>.imagery_clean" \
    --reader_name sgli_l1b_hdf5 \
    --product_name IR-RGB \
    --filename_formatter geoips_fname \
    --output_formatter  imagery_clean \
    --minimum_coverage 0 \
    --sector_list korea 

retval=$?

exit $retval
