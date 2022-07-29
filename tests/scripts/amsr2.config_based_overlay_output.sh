#!/bin/bash

run_procflow ${GEOIPS_TESTDATA_DIR}/test_data_amsr2/data/20200518.062048.gcom-w1.amsr2.amsr2_nesdismanatigcom.x.x.mbt.x.e202005180759470_c202005180937100.nc \
  --procflow config_based \
  --output_config ${GEOIPS_PACKAGES_DIR}/geoips/tests/yaml_configs/amsr2_test.yaml \
  --fuse_files ${GEOIPS_TESTDATA_DIR}/test_data_amsr2/bg_data/ahi_20200518_0740/* \
  --fuse_reader ahi_hsd \
  --fuse_product Visible \
  --fuse_resampled_read True

config_retval=$?

# Produce an overall return value, sum of all 3
exit $((config_retval))
