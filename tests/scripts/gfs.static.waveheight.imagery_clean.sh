# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_gfs/data/gfswave.t06z.wcoast.0p16.f000.grib2 \
    --procflow single_source \
    --reader_name gfs_grib \
    --output_formatter imagery_clean \
    --filename_formatter geoips_fname \
    --sector_list conus \
    --minimum_coverage 0 \
    --product_name Model-WaveHeight \
    --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/gfs.static.waveheight.imagery_clean" 

ss_retval=$?

exit $((ss_retval))
