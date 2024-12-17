# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/sh

$GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/full_install.sh exit_on_missing
if [[ "$?" != "0" ]]; then
    exit 1
fi
echo ""

# This should contain test calls to cover ALL required functionality tests for
# all available geoips plugin repositories on github.com

# The $GEOIPS_PACKAGES_DIR/geoips tests modules sourced within this script handle:
   # setting up the appropriate associative arrays for tracking the overall return value,
   # calling the test scripts appropriately, and
   # setting the final return value.

# Note you must use the variable "call" in the for the loop

# Argument to test_all_pre.sh ONLY sets the prefix on the log output / filenames.
# Used for clarity, and to differentiate potentially multiple "test_all.sh" scripts in
# the same repo.

# For clarity, make the last directory "geoips"
geoips_repopath=`dirname $0`/../../
geoips_pkgname=geoips

recenter_tc_repopath=$GEOIPS_PACKAGES_DIR/recenter_tc
recenter_tc_pkgname=recenter_tc

data_fusion_repopath=$GEOIPS_PACKAGES_DIR/data_fusion
data_fusion_pkgname=data_fusion

template_basic_plugin_repopath=$GEOIPS_PACKAGES_DIR/template_basic_plugin
template_basic_plugin_pkgname=my_package

geoips_plugin_example_repopath=$GEOIPS_PACKAGES_DIR/geoips_plugin_example
geoips_plugin_example_pkgname=geoips_plugin_example

geoips_clavrx_repopath=$GEOIPS_PACKAGES_DIR/geoips_clavrx
geoips_clavrx_pkgname=geoips_clavrx

. $geoips_repopath/tests/utils/test_all_pre.sh ${geoips_pkgname}_full

echo ""
# "call" used in test_all_run.sh
for call in \
  "export GEOIPS_DISABLE_SHARED_CODE_CHECKS=False" \
  "$geoips_repopath/tests/utils/check_code.sh all $geoips_repopath" \
  "export GEOIPS_DISABLE_SHARED_CODE_CHECKS=True" \
  "$geoips_repopath/tests/utils/check_code.sh all $recenter_tc_repopath" \
  "$geoips_repopath/docs/build_docs.sh $geoips_repopath $geoips_pkgname html_only" \
  "$geoips_repopath/docs/build_docs.sh $recenter_tc_repopath $recenter_tc_pkgname html_only" \
  "$geoips_repopath/docs/build_docs.sh $data_fusion_repopath $data_fusion_pkgname html_only" \
  "$geoips_repopath/docs/build_docs.sh $template_basic_plugin_repopath $template_basic_plugin_pkgname html_only" \
  "$geoips_repopath/tests/scripts/abi.static.Infrared.imagery_annotated.sh" \
  "$geoips_repopath/tests/scripts/console_script_create_sector_image.sh" \
  "$geoips_repopath/tests/scripts/console_script_list_available_plugins.sh" \
  "$geoips_repopath/tests/scripts/abi.static.Visible.imagery_annotated.sh" \
  "$geoips_repopath/tests/scripts/abi.static.nasa_dust_rgb.imagery_annotated.sh" \
  "$geoips_repopath/tests/scripts/abi.config_based_output_low_memory.sh" \
  "$geoips_repopath/tests/scripts/abi.config_based_output.sh" \
  "$geoips_repopath/tests/scripts/ahi.tc.WV.geotiff.sh" \
  "$geoips_repopath/tests/scripts/ami.static.Infrared.imagery_annotated.sh" \
  "$geoips_repopath/tests/scripts/ami.static.Visible.imagery_annotated.sh" \
  "$geoips_repopath/tests/scripts/ami.static.mst.absdiff-IR-BD.imagery_annotated.sh" \
  "$geoips_repopath/tests/scripts/ami.tc.WV.geotiff.sh" \
  "$geoips_repopath/tests/scripts/ami.WV-Upper.unprojected_image.sh" \
  "$geoips_repopath/tests/scripts/amsr2.global.89H-Physical.cogeotiff.sh" \
  "$geoips_repopath/tests/scripts/amsr2.tc.89H-Physical.imagery_annotated.sh" \
  "$geoips_repopath/tests/scripts/amsr2_ocean.tc.windspeed.imagery_clean.sh" \
  "$geoips_repopath/tests/scripts/amsr2_rss.tc.windspeed.imagery_clean.sh" \
  "$geoips_repopath/tests/scripts/amsr2.config_based_no_compare.sh" \
  "$geoips_repopath/tests/scripts/amsr2.config_based_overlay_output.sh" \
  "$geoips_repopath/tests/scripts/amsr2.config_based_overlay_output_low_memory.sh" \
  "$geoips_repopath/tests/scripts/ascat_knmi.tc.windbarbs.imagery_windbarbs_clean.sh" \
  "$geoips_repopath/tests/scripts/ascat_low_knmi.tc.windbarbs.imagery_windbarbs.sh" \
  "$geoips_repopath/tests/scripts/ascat_noaa_25km.tc.windbarbs.imagery_windbarbs.sh" \
  "$geoips_repopath/tests/scripts/ascat_noaa_50km.tc.wind-ambiguities.imagery_windbarbs.sh" \
  "$geoips_repopath/tests/scripts/ascat_uhr.tc.wind-ambiguities.imagery_windbarbs.sh" \
  "$geoips_repopath/tests/scripts/ascat_uhr.tc.nrcs.imagery_clean.sh" \
  "$geoips_repopath/tests/scripts/ascat_uhr.tc.windbarbs.imagery_windbarbs.sh" \
  "$geoips_repopath/tests/scripts/ascat_uhr.tc.windspeed.imagery_clean.sh" \
  "$geoips_repopath/tests/scripts/cli_dummy_script.sh" \
  "$geoips_repopath/tests/scripts/gmi.tc.89pct.imagery_clean.sh" \
  "$geoips_repopath/tests/scripts/imerg.tc.Rain.imagery_clean.sh" \
  "$geoips_repopath/tests/scripts/oscat_knmi.tc.windbarbs.imagery_windbarbs.sh" \
  "$geoips_repopath/tests/scripts/sar.tc.nrcs.imagery_annotated.sh" \
  "$geoips_repopath/tests/scripts/smap.unsectored.text_winds.sh" \
  "$geoips_repopath/tests/scripts/viirsday.global.Night-Vis-IR.cogeotiff_rgba.sh" \
  "$geoips_repopath/tests/scripts/viirsday.tc.Night-Vis-IR.imagery_annotated.sh" \
  "$geoips_repopath/tests/scripts/viirsmoon.tc.Night-Vis-GeoIPS1.imagery_clean.sh" \
  "$geoips_repopath/tests/scripts/viirsclearnight.Night-Vis-IR-GeoIPS1.unprojected_image.sh" \
  "$recenter_tc_repopath/tests/scripts/abi.tc.Visible.imagery_clean.sh" \
  "$recenter_tc_repopath/tests/scripts/amsr2.tc.color37.imagery_clean.sh" \
  "$recenter_tc_repopath/tests/scripts/amsr2.tc.windspeed.imagery_clean.sh" \
  "$recenter_tc_repopath/tests/scripts/ascat_uhr.tc.nrcs.imagery_clean.sh" \
  "$recenter_tc_repopath/tests/scripts/ascat_uhr.tc.windbarbs.imagery_clean.sh" \
  "$recenter_tc_repopath/tests/scripts/imerg.tc.Rain.imagery_clean.sh" \
  "$recenter_tc_repopath/tests/scripts/metopc_knmi_125.tc.windbarbs.imagery_clean.sh" \
  "$recenter_tc_repopath/tests/scripts/oscat.tc.windspeed.imagery_clean.sh" \
  "$recenter_tc_repopath/tests/scripts/sar.tc.nrcs.imagery_clean.sh" \
  "$recenter_tc_repopath/tests/scripts/smap.tc.windspeed.imagery_clean.sh" \
  "$recenter_tc_repopath/tests/scripts/viirs.tc.Infrared-Gray.imagery_clean.sh" \
  "$template_basic_plugin_repopath/tests/test_all.sh" \
  "$geoips_plugin_example_repopath/tests/test_all.sh" \
  "$geoips_clavrx_repopath/tests/test_all.sh" \
  "$data_fusion_repopath/tests/test_all.sh"
do
  . $geoips_repopath/tests/utils/test_all_run.sh
done

. $geoips_repopath/tests/utils/test_all_post.sh
