# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/sh

# This should contain test calls to cover ALL required functionality
# tests for this repo.

# The $GEOIPS_PACKAGES_DIR/geoips tests modules sourced within this script handle:
   # setting up the appropriate associative arrays for tracking the overall
   #   return value,
   # calling the test scripts appropriately, and
   # setting the final return value.

repopath=`dirname $0`/../
pkgname=geoips
# Argument to test_all_pre.sh ONLY sets the prefix on the log output / filenames.
# Used for clarity, and to differentiate potentially multiple "test_all.sh" scripts
# in the same repo.
. $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_all_pre.sh ${pkgname}_all

echo ""
# These are only the test scripts that are not included in full_test.sh
# Note you must use the variable "call" in the for the loop
# "call" used in test_all_run.sh
for call in \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/abi.config_based_dmw_overlay.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/abi.static.dmw.imagery_windbarbs_high.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/amsub_mirs.tc.183-3H.imagery_annotated.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/atms.tc.165H.netcdf_geoips.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ewsg.static.Infrared.imagery_clean.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/fci.static.Visible.imagery_annotated.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/fci.unprojected_image.Infrared.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/hy2.tc.windspeed.imagery_annotated.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/mimic_coarse.static.TPW-CIMSS.imagery_annotated.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/mimic_fine.tc.TPW-PWAT.imagery_annotated.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/modis.Infrared.unprojected_image.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/saphir.tc.183-3HNearest.imagery_annotated.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/seviri.WV-Upper.unprojected_image.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/seviri.airmass.imagery_clean.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/seviri.Convective_Storms.imagery_clean.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/seviri.Day_Microphys_Summer.imagery_clean.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/seviri.Day_Microphys_Winter.imagery_clean.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/seviri.Day_Solar.imagery_clean.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/seviri.Dust_RGB.imagery_clean.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/seviri.Natural_Color.imagery_clean.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/seviri.Night_Microphys.imagery_clean.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/seviri.Volcanic_Ash.imagery_clean.sh"
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/smap.unsectored.text_winds.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/smos.tc.sectored.text_winds.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ssmi.tc.37pct.imagery_clean.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ssmis.color91.unprojected_image.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/gfs.static.windspeed.imagery_clean.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/gfs.static.waveheight.imagery_clean.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/viirs.static.visible.imagery_clean.sh"
do
  . $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_all_run.sh
done

. $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_all_post.sh
