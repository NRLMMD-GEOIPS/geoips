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

geoips run \
  $GEOIPS_TESTDATA_DIR/test_data_abi_day/data/goes17_20210718_0150/OR_ABI-L1b*.nc \
  --procflow config_based \
  --output_config $GEOIPS_PACKAGES_DIR/geoips/tests/yaml_configs/abi_test_low_memory.yaml
config_retval=$?

# Produce an overall return value, sum of all 3
exit $((config_retval))
