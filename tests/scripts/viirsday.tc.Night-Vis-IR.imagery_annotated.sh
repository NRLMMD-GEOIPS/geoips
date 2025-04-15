# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210209/073600/VJ102DNB.A2021040.0736.002.2021040145245.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210209/073600/VJ102MOD.A2021040.0736.002.2021040145245.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210209/073600/VJ103DNB.A2021040.0736.002.2021040142228.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210209/073600/VJ103MOD.A2021040.0736.002.2021040142228.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210209/074200/VJ102DNB.A2021040.0742.002.2021040143010.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210209/074200/VJ102MOD.A2021040.0742.002.2021040143010.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210209/074200/VJ103DNB.A2021040.0742.002.2021040140938.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210209/074200/VJ103MOD.A2021040.0742.002.2021040140938.nc \
             --reader_name viirs_netcdf \
             --product_name Night-Vis-IR \
             --filename_formatter tc_fname \
             --output_formatter imagery_annotated \
             --feature_annotator tc_visir \
             --gridline_annotator tc_visir \
             --metadata_filename_formatter metadata_default_fname \
             --metadata_output_formatter metadata_default \
             --trackfile_parser bdeck_parser \
             --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bsh192021.dat \
             --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/viirsday.tc.<product>.imagery_annotated" \
             --product_spec_override '{}' \
             --output_formatter_kwargs '{}' \
             --filename_formatter_kwargs '{}' \
             --metadata_output_formatter_kwargs '{}' \
             --metadata_filename_formatter_kwargs '{}'
ss_retval=$?

exit $((ss_retval))
