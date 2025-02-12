# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

geoips run single_source $GEOIPS_PACKAGES_DIR/test_data_viirs/data/j02_sdr_20240925/*.h5 \
    --procflow single_source \
    --reader_name viirs_sdr_hdf5 \
    --output_formatter imagery_clean \
    --filename_formatter geoips_fname \
    --sector_list se_asia \
    --minimum_coverage 0 \
    --product_name Visible \
    --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/viirs.static.visible.imagery_clean" 

ss_retval=$?

exit $((ss_retval))
