# # # Distribution Statement A. Approved for public release. Distribution is unlimited.
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

#!/bin/bash

test_exit=""
install_script=""
if [[ "$1" == "exit_on_missing" ]]; then
    test_exit="exit_on_missing"
    install_script="$0"
fi

. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh geoips_full
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh ancillary_data cartopy_shapefiles $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo geoips $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo data_fusion $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo recenter_tc $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo geoips_clavrx $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo geoips_plugin_example $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo template_basic_plugin $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo template_fusion_plugin $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh settings_repo .vscode $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_noaa_aws $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_amsr2 $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_clavrx $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_gpm $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_sar $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_scat $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_smap $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_viirs $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data test_data_fusion $test_exit $install_script
create_plugin_registries
