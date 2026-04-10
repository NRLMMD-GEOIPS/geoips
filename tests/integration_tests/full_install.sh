# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

echo "GEOIPS_MODIFIED_BRANCH: $GEOIPS_MODIFIED_BRANCH"

# This script ensures we exit non-zero if any of the steps fail.
check="$GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh"

test_exit=""
install_script=""
skip_create_registries="false"
if [[ "$1" == "exit_on_missing" ]]; then
    test_exit="exit_on_missing"
    install_script="$0"
fi
if [[ "$2" == "skip_create_registries" ]]; then
    skip_create_registries="true"
fi

. $check geoips_full
# Includes test_data_amsr2 and geoips repo
. $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/base_install.sh
. $check ancillary_data cartopy_shapefiles $test_exit $install_script

# Reference repos (non geoips plugin-packages)
. $check settings_repo .vscode $test_exit $install_script
. $check settings_repo .github $test_exit $install_script
. $check settings_repo geoips_ci $test_exit $install_script

# Test data repos required to run tests in geoips repo.
. $check run_command "geoips config install test_data_abi"
. $check run_command "geoips config install test_data_ahi"
. $check run_command "geoips config install test_data_ami"
. $check run_command "geoips config install test_data_amsub"
. $check run_command "geoips config install test_data_arctic_weather_satellite"
. $check run_command "geoips config install test_data_atms"
. $check run_command "geoips config install test_data_cygnss"
. $check run_command "geoips config install test_data_fci"
. $check run_command "geoips config install test_data_gfs"
. $check run_command "geoips config install test_data_gpm"
. $check run_command "geoips config install test_data_modis"
. $check run_command "geoips config install test_data_multi_scan_times"
# . $check run_command "geoips config install test_data_nucaps"
. $check run_command "geoips config install test_data_pyrocb"
. $check run_command "geoips config install test_data_saphir"
. $check run_command "geoips config install test_data_sar"
. $check run_command "geoips config install test_data_scat"
# . $check run_command "geoips config install test_data_sgli"
. $check run_command "geoips config install test_data_seviri"
. $check run_command "geoips config install test_data_smap"
. $check run_command "geoips config install test_data_smos"
. $check run_command "geoips config install test_data_tpw"
. $check run_command "geoips config install test_data_viirs"

if [[ "$skip_create_registries" == "true" ]]; then
    echo "Skipping pluginify create"
else
    pluginify create -n geoips.plugin_packages
fi
