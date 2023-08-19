# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

#!/bin/sh

# This should contain test calls to cover ALL required functionality
# tests for the geoips repo.

# The $GEOIPS_PACKAGES_DIR/geoips tests modules sourced within this script handle:
   # setting up the appropriate associative arrays for tracking the overall
   #   return value,
   # calling the test scripts appropriately, and
   # setting the final return value.

geoips_repopath=$GEOIPS_PACKAGES_DIR/geoips

repopath=`dirname $0`/../
pkgname=geoips

. $geoips_repopath/tests/utils/test_all_pre.sh ${pkgname}_all

echo ""
# Note you must use the variable "call" in the for the loop
# "call" used in test_all_run.sh
for call in \
  "$geoips_repopath/tests/utils/check_code.sh all $repopath flake8_docstring_only" \
  "$geoips_repopath/docs/build_docs.sh $repopath $pkgname html_only" \
  "$geoips_repopath/tests/scripts/abi.static.Visible.imagery_annotated.sh" \
  "$geoips_repopath/tests/scripts/ahi.tc.WV.geotiff.sh" \
  "$geoips_repopath/tests/scripts/amsr2.tc.89H-Physical.imagery_annotated.sh" \
  "$geoips_repopath/tests/scripts/amsr2_ocean.tc.windspeed.imagery_clean.sh" \
  "$geoips_repopath/tests/scripts/amsr2.config_based_overlay_output.sh" \
  "$geoips_repopath/tests/scripts/amsr2.config_based_overlay_output_low_memory.sh" \
  "$geoips_repopath/tests/scripts/amsub_mirs.tc.183-3H.imagery_annotated.sh" \
  "$geoips_repopath/tests/scripts/ascat_knmi.tc.windbarbs.imagery_windbarbs_clean.sh" \
  "$geoips_repopath/tests/scripts/ascat_low_knmi.tc.windbarbs.imagery_windbarbs.sh" \
  "$geoips_repopath/tests/scripts/ascat_noaa_25km.tc.windbarbs.imagery_windbarbs.sh" \
  "$geoips_repopath/tests/scripts/ascat_noaa_50km.tc.windbarbs.imagery_windbarbs.sh" \
  "$geoips_repopath/tests/scripts/ascat_uhr.tc.wind-ambiguities.imagery_windbarbs.sh" \
  "$geoips_repopath/tests/scripts/atms.tc.165H.netcdf_geoips.sh" \
  "$geoips_repopath/tests/scripts/ewsg.static.Infrared.imagery_clean.sh" \
  "$geoips_repopath/tests/scripts/gmi.tc.89pct.imagery_clean.sh" \
  "$geoips_repopath/tests/scripts/hy2.tc.windspeed.imagery_annotated.sh" \
  "$geoips_repopath/tests/scripts/imerg.tc.Rain.imagery_clean.sh" \
  "$geoips_repopath/tests/scripts/mimic_coarse.static.TPW-CIMSS.imagery_annotated.sh" \
  "$geoips_repopath/tests/scripts/mimic_fine.tc.TPW-PWAT.imagery_annotated.sh" \
  "$geoips_repopath/tests/scripts/modis.Infrared.unprojected_image.sh" \
  "$geoips_repopath/tests/scripts/oscat_knmi.tc.windbarbs.imagery_windbarbs.sh" \
  "$geoips_repopath/tests/scripts/saphir.tc.183-3HNearest.imagery_annotated.sh" \
  "$geoips_repopath/tests/scripts/sar.tc.nrcs.imagery_annotated.sh" \
  "$geoips_repopath/tests/scripts/seviri.WV-Upper.unprojected_image.sh" \
  "$geoips_repopath/tests/scripts/smap.unsectored.text_winds.sh" \
  "$geoips_repopath/tests/scripts/smos.tc.sectored.text_winds.sh" \
  "$geoips_repopath/tests/scripts/ssmi.tc.37pct.imagery_clean.sh" \
  "$geoips_repopath/tests/scripts/ssmis.color91.unprojected_image.sh" \
  "$geoips_repopath/tests/scripts/viirsday.tc.Night-Vis-IR.imagery_annotated.sh" \
  "$geoips_repopath/tests/scripts/viirsmoon.tc.Night-Vis-GeoIPS1.imagery_clean.sh" \
  "$geoips_repopath/tests/scripts/viirsclearnight.Night-Vis-IR-GeoIPS1.unprojected_image.sh"
do
  . $geoips_repopath/tests/utils/test_all_run.sh
done

. $geoips_repopath/tests/utils/test_all_post.sh
