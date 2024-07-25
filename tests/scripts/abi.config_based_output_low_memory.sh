# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

geoips run config_based \
             --output_config $GEOIPS_PACKAGES_DIR/geoips/tests/yaml_configs/abi_test_low_memory.yaml
config_retval=$?

# Produce an overall return value, sum of all 3
exit $((config_retval))
