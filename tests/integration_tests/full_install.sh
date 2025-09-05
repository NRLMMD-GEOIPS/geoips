# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

echo "GEOIPS_MODIFIED_BRANCH: $GEOIPS_MODIFIED_BRANCH"

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
# Includes test_data_amsr2 and geoips repo
. $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/base_install.sh
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh ancillary_data cartopy_shapefiles $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh settings_repo .vscode $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_noaa_aws $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_multi_scan_times $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_gpm $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_sar $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_scat $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_smap $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_seviri $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_viirs $test_exit $install_script

if [[ "$include_reference_repos" == "true" ]]; then
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh settings_repo .github $test_exit $install_script
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh settings_repo geoips_ci $test_exit $install_script
  # These may not currently be on cira nexcloud
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data_github template_test_data $test_exit $install_script
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data_github test_data_modis $test_exit $install_script
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data_github test_data_smos $test_exit $install_script
  . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data_github test_data_tpw $test_exit $install_script
fi

create_plugin_registries

