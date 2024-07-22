# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_hy2/data/hscat_20211202_080644_hy_2b__15571_o_250_2204_ovw_l2.nc \
          --reader_name scat_knmi_winds_netcdf \
          --product_name windspeed \
          --filename_formatter tc_fname \
          --output_formatter imagery_annotated \
          --feature_annotator default \
          --gridline_annotator default \
          --metadata_filename_formatter metadata_default_fname \
          --metadata_output_formatter metadata_default \
          --trackfile_parser bdeck_parser \
          --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bwp272021.dat \
          --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/hy2.tc.<product>.imagery_annotated" \
          --product_spec_override '{}' \
          --output_formatter_kwargs '{"title_formatter": "tc_copyright", "title_copyright": "Data copyright 2021 EUMETSAT, Imagery NRL-MRY"}' \
          --filename_formatter_kwargs '{}' \
          --metadata_output_formatter_kwargs '{}' \
          --metadata_filename_formatter_kwargs '{}'
ss_retval=$?

exit $((ss_retval))
