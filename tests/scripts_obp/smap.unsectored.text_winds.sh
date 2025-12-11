# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

set -eu

geoips run order_based -f $GEOIPS_PACKAGES_DIR/geoips/tests/scripts_obp/smap.unsectored.text_winds.yaml   \
          $GEOIPS_TESTDATA_DIR/test_data_smap/data/RSS_smap_wind_daily_2021_09_26_NRT_v01.0.nc

exit $?
