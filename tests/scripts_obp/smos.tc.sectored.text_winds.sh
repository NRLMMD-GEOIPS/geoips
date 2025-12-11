# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

set -eu

geoips run order_based -f "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts_obp/smos.tc.sectored.text_winds.yaml"   \
          $GEOIPS_TESTDATA_DIR/test_data_smos/data/SM_OPER_MIR_SCNFSW_20200216T120839_20200216T135041_110_001_7.nc

exit $?

