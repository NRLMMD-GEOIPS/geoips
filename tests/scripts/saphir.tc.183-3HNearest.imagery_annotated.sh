# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_saphir/data/MT1SAPSL1A__1.09_000_1_19_I_2021_02_09_00_30_03_2021_02_09_01_11_16_48144_48144_497_33_33_KUX_00.h5 \
          --reader_name saphir_hdf5 \
          --product_name 183-3HNearest \
          --filename_formatter tc_fname \
          --output_formatter imagery_annotated \
          --feature_annotator tc_pmw \
          --gridline_annotator tc_pmw \
          --metadata_filename_formatter metadata_default_fname \
          --metadata_output_formatter metadata_default \
          --trackfile_parser bdeck_parser \
          --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bsh192021.dat \
          --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/saphir.tc.183-3HNearest.imagery_annotated" \
          --product_spec_override '{}' \
          --output_formatter_kwargs '{}' \
          --filename_formatter_kwargs '{}' \
          --metadata_output_formatter_kwargs '{}' \
          --metadata_filename_formatter_kwargs '{}'
ss_retval=$?

exit $((ss_retval))
