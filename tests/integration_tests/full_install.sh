# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

test_exit=""
install_script=""
if [[ "$1" == "exit_on_missing" ]]; then
    test_exit="exit_on_missing"
    install_script="$0"
fi
if [[ "$1" == "include_reference_repos" ]]; then
    include_reference_repos="true"
fi

. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh geoips_full
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh ancillary_data cartopy_shapefiles $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo geoips $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo data_fusion $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo recenter_tc $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo geoips_clavrx $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo geoips_plugin_example $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo template_basic_plugin $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh settings_repo .vscode $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_noaa_aws $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_multi_scan_times $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_amsr2 $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_clavrx $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_gpm $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_sar $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_scat $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_smap $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_seviri $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_viirs $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_fusion $test_exit $install_script

if [[ "$include_reference_repos" == "true" ]]; then
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh settings_repo .github $test_exit $install_script
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh settings_repo geoips_ci $test_exit $install_script
  # Currently these need to be installed in this order, until the fortran pyproject.toml builds are working.
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo fortran_utils $test_exit $install_script
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo rayleigh $test_exit $install_script
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo ancildat $test_exit $install_script
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo synth_green $test_exit $install_script
  # The above fortran packages need to be installed BEFORE installing geocolor, lunarref, or true_color
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo geocolor $test_exit $install_script
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo lunarref $test_exit $install_script
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo true_color $test_exit $install_script
  # These may not currently be on github.com
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo ryglickicane $test_exit $install_script
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo tc_mint $test_exit $install_script
  # These may not currently be on cira nexcloud
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data_github template_test_data $test_exit $install_script
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data_github test_data_mint $test_exit $install_script
  # This one takes forever, skip for now.
  # . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data_github test_data_mint_analysis $test_exit $install_script
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data_github test_data_modis $test_exit $install_script
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data_github test_data_smos $test_exit $install_script
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data_github test_data_tpw $test_exit $install_script
fi

create_plugin_registries
