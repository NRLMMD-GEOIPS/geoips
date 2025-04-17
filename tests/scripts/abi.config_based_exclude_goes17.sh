# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

geoips run config_based \
  $GEOIPS_TESTDATA_DIR/test_data_abi_day/data/goes17_20210718_0150/OR_ABI-L1b*.nc \
  --output_config $GEOIPS_PACKAGES_DIR/geoips/tests/yaml_configs/abi_test_low_memory.yaml
config_retval=$?

# Produce an overall return value, sum of all 3
exit $((config_retval))
