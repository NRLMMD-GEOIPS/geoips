#!/bin/bash

# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

# cspell:ignore cfnoc sdris

set -eu

geoips run order_based -f $GEOIPS_PACKAGES_DIR/geoips/tests/scripts_obp/ssmis.color91.unprojected_image.sh   \
          $GEOIPS_TESTDATA_DIR/test_data_ssmis/data/US058SORB-RAWspp.sdris_f16_d20200519_s084400_e102900_r85579_cfnoc.raw

exit $?

