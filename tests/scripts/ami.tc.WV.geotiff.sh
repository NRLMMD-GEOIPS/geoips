#!/bin/bash

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

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
run_procflow $GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/geokompsat/20231208/0300/*.nc \
          --procflow single_source \
          --reader_name ami_netcdf \
          --product_name WV \
          --filename_formatter geotiff_fname \
          --output_formatter geotiff_standard \
          --trackfile_parser bdeck_parser \
          --trackfiles $GEOIPS_TESTDATA_DIR/test_data_geokompsat/sectors/bsh032024.dat \
          --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/ami.tc.<product>.geotiff" \
          --resampled_read
retval=$?

exit $retval
