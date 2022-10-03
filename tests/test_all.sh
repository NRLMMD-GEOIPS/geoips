# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # # 
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # # 
# # # This program is free software:
# # # you can redistribute it and/or modify it under the terms
# # # of the NRLMMD License included with this program.
# # # 
# # # If you did not receive the license, see
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/
# # # for more information.
# # # 
# # # This program is distributed WITHOUT ANY WARRANTY;
# # # without even the implied warranty of MERCHANTABILITY
# # # or FITNESS FOR A PARTICULAR PURPOSE.
# # # See the included license for more details.

#!/bin/sh

# This should contain test calls to cover ALL required functionality tests for the geoips repo.

# The $GEOIPS tests modules sourced within this script handle:
   # setting up the appropriate associative arrays for tracking the overall return value,
   # calling the test scripts appropriately, and 
   # setting the final return value.

# Note you must use the variable "call" in the for the loop

# This calls the full "test_base_install.sh" script - so we ensure it is fully tested via test_all.sh
$GEOIPS_PACKAGES_DIR/geoips/tests/test_base_install.sh

. $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_all_pre.sh geoips_all

# Do not include the calls that are in "test_base_install.sh" within this list.  They are tested above.
echo ""
# "call" used in test_all_run.sh
for call in \
            "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/abi.static.Visible.imagery_annotated.sh" \
            "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ahi.tc.WV.geotiff.sh" \
            "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/amsr2.tc.89H-Physical.imagery_annotated.sh" \
            "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/amsub_mirs.tc.183-3H.imagery_annotated.sh" \
            "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ascat_knmi.tc.windbarbs.imagery_windbarbs_clean.sh" \
            "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ascat_low_knmi.tc.windbarbs.imagery_windbarbs.sh" \
            "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ascat_uhr.tc.wind-ambiguities.imagery_windbarbs.sh" \
            "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/atms.tc.165H.netcdf_geoips.sh" \
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
            "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/ssmis.color89.unprojected_image.sh" \
            "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/viirsday.tc.Night-Vis-IR.imagery_annotated.sh" \
            "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/viirsmoon.tc.Night-Vis-GeoIPS1.imagery_clean.sh" \
            "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/viirsclearnight.Night-Vis-IR-GeoIPS1.unprojected_image.sh"
do
    . $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_all_run.sh
done

. $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_all_post.sh
