# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
# https://www.nrlmry.navy.mil/tcdat/tc2021/WP/WP022021/txt/SCT_winds_knmi_metop-c_WP02_202104210141
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_scat/data/20230524_metopc_noaa_class_tc2023wp02mawar/L2OVW25kmASCAT_v1r1_m03_*.nc \
          --reader_name scat_noaa_winds_netcdf \
          --product_name windbarbs \
          --filename_formatter tc_fname \
          --output_formatter imagery_windbarbs \
          --metadata_filename_formatter metadata_default_fname \
          --metadata_output_formatter metadata_default \
          --trackfile_parser bdeck_parser \
          --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bwp022023.dat \
          --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/ascat_noaa_25km.tc.windbarbs.imagery_windbarbs" \
          --tc_spec_template tc_web_ascat_low_barbs \
          --product_spec_override '{}' \
          --output_formatter_kwargs '{}' \
          --filename_formatter_kwargs '{}' \
          --metadata_output_formatter_kwargs '{}' \
          --metadata_filename_formatter_kwargs '{}'
ss_retval=$?

exit $((ss_retval))
