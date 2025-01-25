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

# For reference, bdeck file with coverage is: $GEOIPS_PACKAGES_DIR/geoips/tests/sectored/bwp202021.dat
# Not used for unsectored output, but potentially for other products
run_procflow $GEOIPS_TESTDATA_DIR/test_data_smap/data/RSS_smap_wind_daily_2024_02_20_NRT_v01.0.nc \
	--procflow single_source \
	--reader_name smap_remss_winds_netcdf \
	--product_name unsectored \
	--output_formatter windspeed_awips2_formatter \
	--output_formatter_kwargs '{"working_directory":"/tmp/"}'
ss_retval=$?

exit $((ss_retval))
