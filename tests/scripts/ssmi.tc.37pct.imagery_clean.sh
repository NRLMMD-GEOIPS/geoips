# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source \
          $GEOIPS_TESTDATA_DIR/test_data_ssmi/data/US058SORB-DEFspp.sdrmi_f15_d20200519_s080800_e095300_r05633_cfnoc.def \
          $GEOIPS_TESTDATA_DIR/test_data_ssmi/data/US058SORB-DEFspp.tdrmi_f15_d20200519_s080800_e095300_r05633_cfnoc.def \
          --reader_name ssmi_binary \
          --product_name 37pct \
          --filename_formatter tc_clean_fname \
          --output_formatter imagery_clean \
          --metadata_filename_formatter metadata_default_fname \
          --metadata_output_formatter metadata_default \
          --trackfile_parser bdeck_parser \
          --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bio012020.dat \
          --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/ssmi.tc.37pct.imagery_clean" \
          --product_spec_override '{}' \
          --output_formatter_kwargs '{}' \
          --filename_formatter_kwargs '{}' \
          --metadata_output_formatter_kwargs '{}' \
          --metadata_filename_formatter_kwargs '{}'
ss_retval=$?

exit $((ss_retval))
