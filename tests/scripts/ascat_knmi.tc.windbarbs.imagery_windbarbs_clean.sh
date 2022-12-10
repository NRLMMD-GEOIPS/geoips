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
# https://www.nrlmry.navy.mil/tcdat/tc2021/WP/WP022021/txt/SCT_winds_knmi_metop-c_WP02_202104210141
run_procflow $GEOIPS_BASEDIR/test_data/test_data_scat/data/metopc_knmi_125/ascat_20210421_010000_metopc_12730_eps_o_coa_3203_ovw.l2.nc \
          --procflow single_source \
          --reader_name scat_knmi_winds_netcdf \
          --product_name windbarbs \
          --filename_format tc_clean_fname \
          --output_format imagery_windbarbs_clean \
          --metadata_filename_format metadata_default_fname \
          --metadata_output_format metadata_default \
          --tc_template_yaml $GEOIPS/geoips/yaml_configs/sectors_dynamic/tc_web_ascat_high_barbs_template.yaml \
          --trackfile_parser bdeck_parser \
          --trackfiles $GEOIPS/tests/sectors/tc_bdecks/bwp022021.dat \
          --compare_path "$GEOIPS/tests/outputs/ascat_knmi.tc.windbarbs.imagery_windbarbs_clean" \
          --product_params_override '{}' \
          --output_format_kwargs '{}' \
          --filename_format_kwargs '{}' \
          --metadata_output_format_kwargs '{}' \
          --metadata_filename_format_kwargs '{}'
ss_retval=$?

exit $((ss_retval))

