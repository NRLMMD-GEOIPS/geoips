# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_amsr2/data/AMSR2-MBT_v2r2_GW1_s202005180620480_e202005180759470_c202005180937100.nc \
          --reader_name amsr2_netcdf \
          --reader_kwargs \
            '{"test_arg": "AMSR2 single source command line reader test_arg"}' \
          --product_name 89H-Physical \
          --filename_formatter tc_fname \
          --output_formatter imagery_annotated \
          --feature_annotator tc_pmw \
          --gridline_annotator tc_pmw \
          --metadata_filename_formatter metadata_default_fname \
          --metadata_output_formatter metadata_default \
          --trackfile_parser bdeck_parser \
          --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bio012020.dat \
          --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/amsr2.tc.<product>.imagery_annotated" \
          --product_spec_override \
            '{"89H-Physical":
              {"coverage_checker":
                {"plugin":
                  {"name": "center_radius", "arguments": {"radius_km": 300}}},
               "interpolator":
                 {"plugin":
                   {"name": "interp_gauss", "arguments": {"nproc": 4}}}
             }}' \
          --output_formatter_kwargs '{}' \
          --filename_formatter_kwargs '{}' \
          --metadata_output_formatter_kwargs '{}' \
          --metadata_filename_formatter_kwargs '{}'
ss_retval=$?

exit $((ss_retval))
