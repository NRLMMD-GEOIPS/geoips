# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# cspell:ignore cfnoc sdrmi

set -eu

geoips run order_based -f $GEOIPS_PACKAGES_DIR/geoips/tests/scripts_obp/smos.awips.netcdf.yaml   \
          $GEOIPS_TESTDATA_DIR/test_data_ssmi/data/US058SORB-DEFspp.sdrmi_f15_d20200519_s080800_e095300_r05633_cfnoc.def \

exit $?
