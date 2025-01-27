# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

geoips run config_based \
  $GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/goes16/20210929/0000/OR_ABI-L2-DMWF*C{07,10,14}*.nc \
  --output_config ${GEOIPS_PACKAGES_DIR}/geoips/tests/yaml_configs/abi_dmw_overlay.yaml \
  --fuse_files ${GEOIPS_TESTDATA_DIR}/test_data_noaa_aws/data/goes16/20210929/0000/*L1b-RadF* \
  --fuse_reader abi_netcdf \
  --fuse_product Infrared-Gray \
  --fuse_resampled_read True

config_retval=$?

# Produce an overall return value, sum of all 3
exit $((config_retval))
