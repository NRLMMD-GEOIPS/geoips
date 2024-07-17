# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_smos/data/SM_OPER_MIR_SCNFSW_20200216T120839_20200216T135041_110_001_7.nc \
             --reader_name smos_winds_netcdf \
             --product_name sectored \
             --filename_formatter text_winds_tc_fname \
             --output_formatter text_winds \
             --trackfile_parser bdeck_parser \
             --trackfiles $GEOIPS_PACKAGES_DIR/geoips/tests/sectors/tc_bdecks/bsh162020.dat \
             --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/smos.tc.sectored.text_winds"
ss_retval=$?

exit $((ss_retval))
