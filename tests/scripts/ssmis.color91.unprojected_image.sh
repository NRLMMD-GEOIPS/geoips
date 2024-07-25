# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_ssmis/data/US058SORB-RAWspp.sdris_f16_d20200519_s084400_e102900_r85579_cfnoc.raw \
          --reader_name ssmis_binary \
          --product_name color91 \
          --output_formatter unprojected_image \
          --filename_formatter geoips_fname \
          --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/ssmis.color91.unprojected_image" \
          --self_register_dataset 'IMAGER' \
          --self_register_source ssmis
retval=$?

exit $retval
