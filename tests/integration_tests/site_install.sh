# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

echo "GEOIPS_MODIFIED_BRANCH: $GEOIPS_MODIFIED_BRANCH"
echo "GEOIPS_USE_PRIVATE_PLUGINS: $GEOIPS_USE_PRIVATE_PLUGINS"

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

. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh geoips_site

# Includes base_install, plus cartopy shapefiles, .vscode repo, and all test data repos required to run tests in geoips repo
. $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/full_install.sh

. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo data_fusion $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo geoips_clavrx $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo geoips_plugin_example $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo recenter_tc $test_exit $install_script

# Private repos - only clone if GEOIPS_USE_PRIVATE_PLUGINS is set to "true"
if [[ "$GEOIPS_USE_PRIVATE_PLUGINS" == "true" ]]; then
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo ryglickicane $test_exit $install_script
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo tc_mint $test_exit $install_script
fi

. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo template_basic_plugin $test_exit $install_script

###########################################
# DO NOT alphabetize plugin packages in this section.
# Currently these need to be installed in this order, until the fortran pyproject.toml builds are working.
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo fortran_utils $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo rayleigh $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo ancildat $test_exit $install_script
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo synth_green $test_exit $install_script

# The above fortran packages need to be installed BEFORE installing geocolor, lunarref, or true_color.
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo geocolor $test_exit $install_script

# Private repos (lunarref and true_color) - only clone if GEOIPS_USE_PRIVATE_PLUGINS is set to "true"
if [[ "$GEOIPS_USE_PRIVATE_PLUGINS" == "true" ]]; then
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo lunarref $test_exit $install_script
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh source_repo true_color $test_exit $install_script
fi
###########################################

# Test data repos required for fully supported plugin packages (above)
geoips config install template_test_data
geoips config install test_data_clavrx
geoips config install test_data_fusion
geoips config install test_data_geocolor
# Takes forever, skip
# geoips config install test_data_mint_analysis

# Private test data - only install if GEOIPS_USE_PRIVATE_PLUGINS is set to "true"
if [[ "$GEOIPS_USE_PRIVATE_PLUGINS" == "true" ]]; then
    geoips config install test_data_mint
fi

if [[ "$skip_create_registries" == "true" ]]; then
    echo "Skipping geoips config create-registries"
else
    geoips config create-registries
fi
