# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source \
          $GEOIPS_TESTDATA_DIR/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/GATMO_j01_d20210809_t0838266_e0838583_b19295_fnmoc_ops.h5 \
          $GEOIPS_TESTDATA_DIR/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/GATMO_j01_d20210809_t0838586_e0839303_b19295_fnmoc_ops.h5 \
          $GEOIPS_TESTDATA_DIR/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/GATMO_j01_d20210809_t0839306_e0840023_b19295_fnmoc_ops.h5 \
          $GEOIPS_TESTDATA_DIR/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/GATMO_j01_d20210809_t0840026_e0840343_b19295_fnmoc_ops.h5 \
          $GEOIPS_TESTDATA_DIR/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/GATMO_j01_d20210809_t0840346_e0841063_b19295_fnmoc_ops.h5 \
          $GEOIPS_TESTDATA_DIR/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/GATMO_j01_d20210809_t0841066_e0841383_b19295_fnmoc_ops.h5 \
          $GEOIPS_TESTDATA_DIR/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/GATMO_j01_d20210809_t0841386_e0842103_b19295_fnmoc_ops.h5 \
          $GEOIPS_TESTDATA_DIR/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/SATMS_j01_d20210809_t0838266_e0838583_b19295_fnmoc_ops.h5 \
          $GEOIPS_TESTDATA_DIR/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/SATMS_j01_d20210809_t0838586_e0839303_b19295_fnmoc_ops.h5 \
          $GEOIPS_TESTDATA_DIR/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/SATMS_j01_d20210809_t0839306_e0840023_b19295_fnmoc_ops.h5 \
          $GEOIPS_TESTDATA_DIR/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/SATMS_j01_d20210809_t0840026_e0840343_b19295_fnmoc_ops.h5 \
          $GEOIPS_TESTDATA_DIR/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/SATMS_j01_d20210809_t0840346_e0841063_b19295_fnmoc_ops.h5 \
          $GEOIPS_TESTDATA_DIR/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/SATMS_j01_d20210809_t0841066_e0841383_b19295_fnmoc_ops.h5 \
          $GEOIPS_TESTDATA_DIR/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/SATMS_j01_d20210809_t0841386_e0842103_b19295_fnmoc_ops.h5 \
          --reader_name atms_hdf5 \
          --product_name 165H \
          --filename_formatter geoips_netcdf_fname \
          --output_formatter netcdf_geoips \
          --trackfile_parser bdeck_parser \
          --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bep112021.dat \
          --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/atms.tc.<product>.netcdf_geoips" \
          --tc_spec_template tc_4km_256x256 \
          --product_spec_override '{}' \
          --output_formatter_kwargs '{"clobber": "True"}' \
          --filename_formatter_kwargs '{}' \
          --metadata_output_formatter_kwargs '{}' \
          --metadata_filename_formatter_kwargs '{}'
ss_retval=$?

exit $((ss_retval))
