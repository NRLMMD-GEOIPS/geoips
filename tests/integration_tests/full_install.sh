# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

echo "GEOIPS_MODIFIED_BRANCH: $GEOIPS_MODIFIED_BRANCH"

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

. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh geoips_full
# Includes test_data_amsr2 and geoips repo
. $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/base_install.sh
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh ancillary_data cartopy_shapefiles $test_exit $install_script

# Reference repos (non geoips plugin-packages)
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh settings_repo .vscode $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh settings_repo .github $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh settings_repo geoips_ci $test_exit $install_script

# Test data repos required to run tests in geoips repo.
geoips config install test_data_amsub
geoips config install test_data_arctic_weather_satellite
geoips config install test_data_atms
geoips config install test_data_cygnss
geoips config install test_data_fci
geoips config install test_data_gfs
geoips config install test_data_gpm
geoips config install test_data_modis
geoips config install test_data_multi_scan_times
geoips config install test_data_saphir
geoips config install test_data_sar
geoips config install test_data_scat
geoips config install test_data_seviri
geoips config install test_data_smap
geoips config install test_data_smos
geoips config install test_data_tpw
geoips config install test_data_viirs
geoips config install test_data_noaa_aws

if [[ "$skip_create_registries" == "true" ]]; then
    echo "Skipping geoips config create-registries"
else
    geoips config create-registries
fi
