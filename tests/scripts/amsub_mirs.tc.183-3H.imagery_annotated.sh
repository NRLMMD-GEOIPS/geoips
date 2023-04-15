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

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
run_procflow $GEOIPS_TESTDATA_DIR/test_data_amsub/data/NPR-MIRS-IMG_v11r4_ma2_s202104192335000_e202104190118000_c202104200206490.nc \
          --procflow single_source \
          --reader_name amsub_mirs \
          --product_name 183-3H \
          --filename_formattertc_fname \
          --output_formatter imagery_annotated \
          --boundaries_params tc_pmw \
          --gridlines_params tc_pmw \
          --metadata_filename_formattermetadata_default_fname \
          --metadata_output_formatter metadata_default \
          --trackfile_parser bdeck_parser \
          --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bwp022021.dat \
          --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/amsub_mirs.tc.<product>.imagery_annotated" \
          --product_params_override '{}' \
          --output_formatter_kwargs '{}' \
          --filename_formatterkwargs '{}' \
          --metadata_output_formatter_kwargs '{}' \
          --metadata_filename_formatterkwargs '{}'
ss_retval=$?

exit $((ss_retval))
