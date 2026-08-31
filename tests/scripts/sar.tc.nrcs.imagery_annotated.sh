# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_sar/data/STAR_SAR_20181025203206_WP312018_31W_FIX_3km.nc \
          --reader_name sar_winds_netcdf \
          --product_name nrcs \
          --filename_formatter tc_fname \
          --output_formatter imagery_annotated \
          --feature_annotator default \
          --gridline_annotator default \
          --metadata_filename_formatter metadata_default_fname \
          --metadata_output_formatter metadata_tc \
          --trackfile_parser bdeck_parser \
          --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bwp312018.dat \
          --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/sar.tc.nrcs.imagery_annotated" \
          --product_spec_override '{}' \
          --output_formatter_kwargs '{"title_formatter": "tc_copyright"}' \
          --filename_formatter_kwargs '{}' \
          --metadata_output_formatter_kwargs '{}' \
          --metadata_filename_formatter_kwargs '{}'
ss_retval=$?

exit $((ss_retval))
