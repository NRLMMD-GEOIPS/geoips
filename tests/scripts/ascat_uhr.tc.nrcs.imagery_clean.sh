# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
# https://www.nrlmry.navy.mil/tcdat/tc2021/WP/WP022021/txt/SCT_winds_knmi_metop-c_WP02_202104210141
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_scat/data/20220911_metopb_byu_uhr_tc2022wp14muifa/MUIFA_20220911_51797_B_A-product.nc \
          --reader_name ascat_uhr_netcdf \
          --product_name nrcs \
          --filename_formatter tc_fname \
          --output_formatter imagery_clean \
          --tc_spec_template tc_web \
          --trackfile_parser bdeck_parser \
          --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bwp142022.dat \
          --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/ascat_uhr.tc.nrcs.imagery_clean" \
          --product_spec_override '{}' \
          --output_formatter_kwargs '{}' \
          --filename_formatter_kwargs '{}' \
          --metadata_output_formatter_kwargs '{}' \
          --metadata_filename_formatter_kwargs '{}' \
          --sector_adjuster_kwargs '{
              "archer_config": {
                  "include_archer_metadata_in_sector_info": True,
                  "required_vmax_kts": 50,
                  "output_products_dict": {
                      "archer_image": {
                          "output_formatter": "archer_image",
                          "filename_formatter": "archer_image",
                      },
                      "archer_fix": {
                          "output_formatter": "archer_fix",
                          "filename_formatter": "archer_fix",
                      }
                  }
              }
          }'
ss_retval=$?

exit $((ss_retval))
