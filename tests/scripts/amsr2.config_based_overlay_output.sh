# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

geoips run config_based ${GEOIPS_TESTDATA_DIR}/test_data_amsr2/data/AMSR2-MBT_v2r2_GW1_s202005180620480_e202005180759470_c202005180937100.nc \
  --output_config ${GEOIPS_PACKAGES_DIR}/geoips/tests/yaml_configs/amsr2_test.yaml \
  --fuse_files ${GEOIPS_TESTDATA_DIR}/test_data_amsr2/bg_data/ahi_20200518_0740/* \
  --fuse_reader ahi_hsd \
  --fuse_product Visible \
  --fuse_resampled_read True

config_retval=$?

# Produce an overall return value, sum of all 3
exit $((config_retval))
