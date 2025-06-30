#!/bin/bash

# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

run_procflow $GEOIPS_TESTDATA_DIR/test_data_abi_day/data/goes16_20200918_1950/* \
    --procflow single_source \
    --reader_name abi_netcdf \
    --resampled_read \
    --product_name GeoColor \
    --output_formatter awips_tiled \
    --sector_list goes_east
retval=$?

exit $retval