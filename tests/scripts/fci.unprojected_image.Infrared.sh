# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_mtg_fci_day/data/mt1_fdhsi_20240113_1150/* \
             --reader_name fci_netcdf \
             --product_name Infrared \
             --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/fci.unprojected_image.<product>" \
             --output_formatter unprojected_image \
             --output_formatter_kwargs '{"x_size": "1000","y_size": "1000"}' \
             --filename_formatter geoips_fname, \
             --reader_kwargs '{"self_register": true}' \
             --self_register_dataset FULL_DISK \
             --self_register_source fci \
             --filename_formatter geoips_fname

retval=$?

exit $retval
