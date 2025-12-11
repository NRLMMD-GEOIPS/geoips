# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

# cspell:ignore DMWVF

set -eu

geoips run order_based -f $GEOIPS_PACKAGES_DIR/geoips/tests/scripts_obp/abi.static.dmw.imagery_windbarbs_high.yaml $GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/goes16/20210929/0000/OR_ABI-L2-DMWVF*.nc

exit $?
