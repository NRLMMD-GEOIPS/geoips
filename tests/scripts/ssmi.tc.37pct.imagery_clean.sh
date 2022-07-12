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
run_procflow \
          $GEOIPS_BASEDIR/test_data/test_data_ssmi/data/US058SORB-DEFspp.sdrmi_f15_d20200519_s080800_e095300_r05633_cfnoc.def \
          $GEOIPS_BASEDIR/test_data/test_data_ssmi/data/US058SORB-DEFspp.tdrmi_f15_d20200519_s080800_e095300_r05633_cfnoc.def \
          --procflow single_source \
          --reader_name ssmi_binary \
          --product_name 37pct \
          --filename_format tc_clean_fname \
          --output_format imagery_clean \
          --metadata_filename_format metadata_default_fname \
          --metadata_output_format metadata_default \
          --trackfile_parser bdeck_parser \
          --trackfiles $GEOIPS/tests/sectors/tc_bdecks/bio012020.dat \
          --compare_path "$GEOIPS/tests/outputs/ssmi.tc.37pct.imagery_clean" \
          --product_params_override '{}' \
          --output_format_kwargs '{}' \
          --filename_format_kwargs '{}' \
          --metadata_output_format_kwargs '{}' \
          --metadata_filename_format_kwargs '{}'
ss_retval=$?

exit $((ss_retval))
