# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # # 
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # # 
# # # This program is free software:
# # # you can redistribute it and/or modify it under the terms
# # # of the NRLMMD License included with this program.
# # # 
# # # If you did not receive the license, see
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/
# # # for more information.
# # # 
# # # This program is distributed WITHOUT ANY WARRANTY;
# # # without even the implied warranty of MERCHANTABILITY
# # # or FITNESS FOR A PARTICULAR PURPOSE.
# # # See the included license for more details.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
run_procflow \
          $GEOIPS_BASEDIR/test_data/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/GATMO_j01_d20210809_t0838266_e0838583_b19295_fnmoc_ops.h5 \
          $GEOIPS_BASEDIR/test_data/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/GATMO_j01_d20210809_t0838586_e0839303_b19295_fnmoc_ops.h5 \
          $GEOIPS_BASEDIR/test_data/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/GATMO_j01_d20210809_t0839306_e0840023_b19295_fnmoc_ops.h5 \
          $GEOIPS_BASEDIR/test_data/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/GATMO_j01_d20210809_t0840026_e0840343_b19295_fnmoc_ops.h5 \
          $GEOIPS_BASEDIR/test_data/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/GATMO_j01_d20210809_t0840346_e0841063_b19295_fnmoc_ops.h5 \
          $GEOIPS_BASEDIR/test_data/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/GATMO_j01_d20210809_t0841066_e0841383_b19295_fnmoc_ops.h5 \
          $GEOIPS_BASEDIR/test_data/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/GATMO_j01_d20210809_t0841386_e0842103_b19295_fnmoc_ops.h5 \
          $GEOIPS_BASEDIR/test_data/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/SATMS_j01_d20210809_t0838266_e0838583_b19295_fnmoc_ops.h5 \
          $GEOIPS_BASEDIR/test_data/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/SATMS_j01_d20210809_t0838586_e0839303_b19295_fnmoc_ops.h5 \
          $GEOIPS_BASEDIR/test_data/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/SATMS_j01_d20210809_t0839306_e0840023_b19295_fnmoc_ops.h5 \
          $GEOIPS_BASEDIR/test_data/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/SATMS_j01_d20210809_t0840026_e0840343_b19295_fnmoc_ops.h5 \
          $GEOIPS_BASEDIR/test_data/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/SATMS_j01_d20210809_t0840346_e0841063_b19295_fnmoc_ops.h5 \
          $GEOIPS_BASEDIR/test_data/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/SATMS_j01_d20210809_t0841066_e0841383_b19295_fnmoc_ops.h5 \
          $GEOIPS_BASEDIR/test_data/test_data_atms/data/jpss-1_20210809_0838_tc2021ep11Kevin/SATMS_j01_d20210809_t0841386_e0842103_b19295_fnmoc_ops.h5 \
          --procflow single_source \
          --reader_name atms_hdf5 \
          --product_name 165H \
          --filename_format geoips_netcdf_fname \
          --output_format netcdf_geoips \
          --trackfile_parser bdeck_parser \
          --trackfiles $GEOIPS/tests/sectors/tc_bdecks/bep112021.dat \
          --compare_path "$GEOIPS/tests/outputs/atms.tc.<product>.netcdf_geoips" \
          --tc_template_yaml $GEOIPS/geoips/yaml_configs/sectors_dynamic/tc_256x256/tc_4km_256x256.yaml \
          --product_params_override '{}' \
          --output_format_kwargs '{}' \
          --filename_format_kwargs '{}' \
          --metadata_output_format_kwargs '{}' \
          --metadata_filename_format_kwargs '{}'
ss_retval=$?

exit $((ss_retval))
