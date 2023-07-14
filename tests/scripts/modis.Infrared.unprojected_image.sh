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
run_procflow $GEOIPS_TESTDATA_DIR/test_data_modis/data/aqua/20210104/200500/MYD021KM.A2021004.2005.061.NRT.hdf \
             $GEOIPS_TESTDATA_DIR/test_data_modis/data/aqua/20210104/200500/MYD03.A2021004.2005.061.NRT.hdf \
             $GEOIPS_TESTDATA_DIR/test_data_modis/data/aqua/20210104/201000/MYD021KM.A2021004.2010.061.NRT.hdf \
             $GEOIPS_TESTDATA_DIR/test_data_modis/data/aqua/20210104/201000/MYD03.A2021004.2010.061.NRT.hdf \
             $GEOIPS_TESTDATA_DIR/test_data_modis/data/aqua/20210104/201500/MYD021KM.A2021004.2015.061.NRT.hdf \
             $GEOIPS_TESTDATA_DIR/test_data_modis/data/aqua/20210104/201500/MYD03.A2021004.2015.061.NRT.hdf \
             --procflow single_source \
             --reader_name modis_hdf4 \
             --product_name Infrared \
             --output_formatter unprojected_image \
             --output_formatter_kwargs '{"x_size": "250"}' \
             --filename_formatter geoips_fname \
             --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/modis.<product>.unprojected_image" \
             --self_register_dataset '1KM' \
             --self_register_source modis
retval=$?

exit $retval
