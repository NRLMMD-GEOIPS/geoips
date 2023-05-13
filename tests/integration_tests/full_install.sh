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

#!/bin/bash

test_exit=""
if [[ "$1" == "exit_on_missing" ]]; then
    test_exit="exit_on_missing"
fi

. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh geoips_base
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh aws_test_data abi_day $test_exit
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh aws_test_data ahi_day $test_exit
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh aws_test_data fusion_data $test_exit
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo data_fusion $test_exit
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo recenter_tc $test_exit
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo geoips_clavrx $test_exit
# . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo geoips_plugin_example $test_exit
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo template_basic_plugin $test_exit
# . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo template_fusion_plugin $test_exit
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_repo test_data_amsr2 $test_exit
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_repo test_data_clavrx $test_exit
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_repo test_data_gpm $test_exit
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_repo test_data_sar $test_exit
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_repo test_data_scat $test_exit
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_repo test_data_smap $test_exit
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_repo test_data_viirs $test_exit

. $GEOIPS_PACKAGES_DIR/geoips/tests/uncompress_test_data.sh
