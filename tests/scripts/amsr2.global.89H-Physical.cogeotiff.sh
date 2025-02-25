# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
run_procflow $GEOIPS_TESTDATA_DIR/test_data_amsr2/data/AMSR2-MBT_v2r2_GW1_s202005180620480_e202005180759470_c202005180937100.nc \
          --procflow single_source \
          --reader_name amsr2_netcdf \
          --product_name 89H-Physical \
          --filename_formatter geotiff_fname \
          --output_formatter cogeotiff \
          --sector_list global_cylindrical \
          --minimum_coverage 0 \
          --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/amsr2.global.<product>.cogeotiff"
ss_retval=$?

exit $((ss_retval))
