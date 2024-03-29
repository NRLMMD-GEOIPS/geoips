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

run_procflow ${GEOIPS_TESTDATA_DIR}/test_data_amsr2/data/AMSR2-MBT_v2r2_GW1_s202005180620480_e202005180759470_c202005180937100.nc \
  --procflow config_based \
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
