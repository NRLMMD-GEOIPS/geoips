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
# Note you must use the variable "call" in the for the loop
# "call" used in test_all_run.sh
for call in \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/utils/check_code.sh all $repopath" \
  "$GEOIPS_PACKAGES_DIR/geoips/docs/build_docs.sh $repopath $pkgname html_only" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/abi.static.Visible.imagery_annotated.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ahi.tc.WV.geotiff.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ami.static.Infrared.imagery_annotated.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ami.static.Visible.imagery_annotated.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ami.tc.WV.geotiff.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ami.WV-Upper.unprojected_image.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/amsr2.tc.89H-Physical.imagery_annotated.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/amsr2_ocean.tc.windspeed.imagery_clean.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/amsr2.config_based_overlay_output.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/amsr2.config_based_overlay_output_low_memory.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/amsub_mirs.tc.183-3H.imagery_annotated.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ascat_knmi.tc.windbarbs.imagery_windbarbs_clean.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ascat_low_knmi.tc.windbarbs.imagery_windbarbs.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ascat_noaa_25km.tc.windbarbs.imagery_windbarbs.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ascat_noaa_50km.tc.wind-ambiguities.imagery_windbarbs.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ascat_uhr.tc.wind-ambiguities.imagery_windbarbs.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ascat_uhr.tc.windbarbs.imagery_windbarbs.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ascat_uhr.tc.windspeed.imagery_clean.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/atms.tc.165H.netcdf_geoips.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/cli_dummy_script.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ewsg.static.Infrared.imagery_clean.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/gmi.tc.89pct.imagery_clean.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/hy2.tc.windspeed.imagery_annotated.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/imerg.tc.Rain.imagery_clean.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/mimic_coarse.static.TPW-CIMSS.imagery_annotated.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/mimic_fine.tc.TPW-PWAT.imagery_annotated.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/modis.Infrared.unprojected_image.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/oscat_knmi.tc.windbarbs.imagery_windbarbs.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/saphir.tc.183-3HNearest.imagery_annotated.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/sar.tc.nrcs.imagery_annotated.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/seviri.WV-Upper.unprojected_image.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/smap.unsectored.text_winds.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/smos.tc.sectored.text_winds.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ssmi.tc.37pct.imagery_clean.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ssmis.color91.unprojected_image.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/viirsclearnight.Night-Vis-IR-GeoIPS1.imagery_annotated.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/viirsday.tc.Night-Vis-IR.imagery_annotated.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/viirsmoon.tc.Night-Vis-GeoIPS1.imagery_clean.sh" \
  "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/viirsclearnight.Night-Vis-IR-GeoIPS1.unprojected_image.sh"
do
  . $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_all_run.sh
done

. $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_all_post.sh
