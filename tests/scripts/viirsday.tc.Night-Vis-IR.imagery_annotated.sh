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

run_procflow $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210209/073600/VJ102DNB.A2021040.0736.002.2021040145245.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210209/073600/VJ102MOD.A2021040.0736.002.2021040145245.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210209/073600/VJ103DNB.A2021040.0736.002.2021040142228.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210209/073600/VJ103MOD.A2021040.0736.002.2021040142228.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210209/074200/VJ102DNB.A2021040.0742.002.2021040143010.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210209/074200/VJ102MOD.A2021040.0742.002.2021040143010.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210209/074200/VJ103DNB.A2021040.0742.002.2021040140938.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210209/074200/VJ103MOD.A2021040.0742.002.2021040140938.nc \
             --procflow single_source \
             --reader_name viirs_netcdf \
             --product_name Night-Vis-IR \
             --filename_format tc_fname \
             --output_format imagery_annotated \
             --boundaries_params tc_visir \
             --gridlines_params tc_visir \
             --metadata_filename_format metadata_default_fname \
             --metadata_output_format metadata_default \
             --trackfile_parser bdeck_parser \
             --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bsh192021.dat \
             --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/viirsday.tc.<product>.imagery_annotated" \
             --product_params_override '{}' \
             --output_format_kwargs '{}' \
             --filename_format_kwargs '{}' \
             --metadata_output_format_kwargs '{}' \
             --metadata_filename_format_kwargs '{}'
ss_retval=$?

exit $((ss_retval))
