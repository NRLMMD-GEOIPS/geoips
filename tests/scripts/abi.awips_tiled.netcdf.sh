#!/bin/bash

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/goes16/20200918/1950/* \
    --reader_name abi_netcdf \
    --product_name Infrared \
    --resampled_read \
    --minimum_coverage 0 \
    --output_formatter awips_tiled \
    --sector_list goes_east \
    --logging_level debug
retval=$?

exit $retval