# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # # 
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # # 
# # # This program is free software:
# # # you can redistribute it and/or modify it under the terms
# # # of the NRLMMD License included with this program.
# # # 
# # # If you did not receive the license, see
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/
# # # for more information.
# # # 
# # # This program is distributed WITHOUT ANY WARRANTY;
# # # without even the implied warranty of MERCHANTABILITY
# # # or FITNESS FOR A PARTICULAR PURPOSE.
# # # See the included license for more details.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
run_procflow $GEOIPS_TESTDATA_DIR/test_data_hy2/data/hscat_20211202_080644_hy_2b__15571_o_250_2204_ovw_l2.nc \
          --procflow single_source \
          --reader_name scat_knmi_winds_netcdf \
          --product_name windspeed \
          --filename_format tc_fname \
          --output_format imagery_annotated \
          --boundaries_params default \
          --gridlines_params default \
          --metadata_filename_format metadata_default_fname \
          --metadata_output_format metadata_default \
          --trackfile_parser bdeck_parser \
          --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bwp272021.dat \
          --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/hy2.tc.<product>.imagery_annotated" \
          --product_params_override '{}' \
          --output_format_kwargs '{"title_format": "tc_copyright", "title_copyright": "Data copyright 2021 EUMETSAT, Imagery NRL-MRY"}' \
          --filename_format_kwargs '{}' \
          --metadata_output_format_kwargs '{}' \
          --metadata_filename_format_kwargs '{}'
ss_retval=$?

exit $((ss_retval))
