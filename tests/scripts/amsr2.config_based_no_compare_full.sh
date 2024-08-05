# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

geoips run config_based ${GEOIPS_TESTDATA_DIR}/test_data_amsr2/data/AMSR2-MBT_v2r2_GW1_s202005180620480_e202005180759470_c202005180937100.nc \
  --output_config ${GEOIPS_PACKAGES_DIR}/geoips/tests/yaml_configs/amsr2_no_compare_full.yaml \
  --trackfile_parser bdeck_parser \
  --trackfiles ${GEOIPS_PACKAGES_DIR}/geoips/tests/sectors/tc_bdecks/bio012020.dat \
  --reader_kwargs \
    '{"test_arg": "Command line config-based amsr2 test arg"}' \
  --fuse_files ${GEOIPS_TESTDATA_DIR}/test_data_amsr2/bg_data/ahi_20200518_0740/* \
  --fuse_reader ahi_hsd \
  --fuse_reader_kwargs \
    '{"test_arg": "Command line config-based ahi test arg"}' \
  --fuse_product Infrared-Gray \
  --fuse_resampled_read True

config_retval=$?

# Produce an overall return value, sum of all 3
exit $((config_retval))
