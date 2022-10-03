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
run_procflow $GEOIPS_TESTDATA_DIR/test_data_gpm/data/1B.GPM.GMI.TB2016.20200917-S171519-E172017.V05A.RT-H5 \
             $GEOIPS_TESTDATA_DIR/test_data_gpm/data/1B.GPM.GMI.TB2016.20200917-S172019-E172517.V05A.RT-H5 \
             $GEOIPS_TESTDATA_DIR/test_data_gpm/data/1B.GPM.GMI.TB2016.20200917-S172519-E173017.V05A.RT-H5 \
             --procflow single_source \
             --reader_name gmi_hdf5 \
             --product_name 89pct \
             --filename_format tc_clean_fname \
             --output_format imagery_clean \
             --metadata_filename_format metadata_default_fname \
             --metadata_output_format metadata_default \
             --trackfile_parser bdeck_parser \
             --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bal202020.dat \
             --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/gmi.tc.<product>.imagery_clean" \
             --product_params_override '{"89pct": {"covg_func": "center_radius", "covg_args": {"radius_km": 300}}}' \
             --output_format_kwargs '{}' \
             --filename_format_kwargs '{}' \
             --metadata_output_format_kwargs '{}' \
             --metadata_filename_format_kwargs '{}'
ss_retval=$?

exit $((ss_retval))
