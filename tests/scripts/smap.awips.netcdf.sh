#!/bin/bash

# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_awips_windspeed/RSS_smap_wind_daily_2024_02_20_NRT_v01.0.nc \
	--reader_name smap_remss_winds_netcdf \
	--product_name unsectored \
	--output_formatter windspeed_awips2_formatter \

ss_retval=$?

exit $((ss_retval))
