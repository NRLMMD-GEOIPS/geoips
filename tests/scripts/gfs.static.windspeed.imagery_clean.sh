# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_gfs/data/gfs.t06z.pgrb2.0p25.f000 \
    --procflow single_source \
    --reader_name gfs_grib \
    --output_formatter imagery_clean \
    --filename_formatter geoips_fname \
    --sector_list himawari \
    --minimum_coverage 0 \
    --product_name Model-Windspeed \
    --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/gfs.static.windspeed.imagery_clean" 

ss_retval=$?

exit $((ss_retval))
