# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_gpm/data/1B.GPM.GMI.TB2016.20200917-S171519-E172017.V05A.RT-H5 \
             $GEOIPS_TESTDATA_DIR/test_data_gpm/data/1B.GPM.GMI.TB2016.20200917-S172019-E172517.V05A.RT-H5 \
             $GEOIPS_TESTDATA_DIR/test_data_gpm/data/1B.GPM.GMI.TB2016.20200917-S172519-E173017.V05A.RT-H5 \
             --reader_name gmi_hdf5 \
             --product_name 89pct \
             --filename_formatter tc_clean_fname \
             --output_formatter imagery_clean \
             --metadata_filename_formatter metadata_default_fname \
             --metadata_output_formatter metadata_default \
             --no_presectoring \
             --trackfile_parser bdeck_parser \
             --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bal202020.dat \
             --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/gmi.tc.<product>.imagery_clean" \
             --product_spec_override '{"89pct": {"coverage_checker": {"plugin": {"name": "center_radius", "arguments": {"radius_km": 300}}}}}' \
             --output_formatter_kwargs '{}' \
             --filename_formatter_kwargs '{}' \
             --metadata_output_formatter_kwargs '{}' \
             --metadata_filename_formatter_kwargs '{}'
ss_retval=$?

exit $((ss_retval))
