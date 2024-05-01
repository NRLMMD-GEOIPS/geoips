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
run_procflow $GEOIPS_TESTDATA_DIR/test_data_geokompsat/data/20231208_0300_daytime/* \
             --procflow single_source \
             --reader_name geokompsat_netcdf \
             --reader_kwargs '{"self_register": "LOW"}' \
             --product_name WV-Upper \
             --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/geokompsat.WV-Upper.unprojected_image" \
             --output_formatter unprojected_image \
             --output_formatter_kwargs '{"x_size": "1000", "y_size": "1000"}' \
             --filename_formatter geoips_fname \
             --logging_level info \
             --self_register_dataset 'Full-Disk' \
             --self_register_source geokompsat
retval=$?

exit $retval
