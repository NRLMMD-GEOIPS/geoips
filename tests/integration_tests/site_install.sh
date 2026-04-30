# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

echo "GEOIPS_MODIFIED_BRANCH: $GEOIPS_MODIFIED_BRANCH"
echo "GEOIPS_USE_PRIVATE_PLUGINS: $GEOIPS_USE_PRIVATE_PLUGINS"

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

. $check geoips_site

# Includes base_install, plus cartopy shapefiles, .vscode repo, and all test data repos required to run tests in geoips repo
. $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/full_install.sh

# . $check source_repo akima86 $test_exit $install_script
. $check source_repo data_fusion $test_exit $install_script
. $check source_repo geoips_clavrx $test_exit $install_script
. $check source_repo geoips_plugin_example $test_exit $install_script
# . $check source_repo geoips_proxyvis $test_exit $install_script
# . $check source_repo geoips_tomorrowio $test_exit $install_script
. $check source_repo geoips_tropics $test_exit $install_script
. $check source_repo recenter_tc $test_exit $install_script
# DO NOT install geoips_tutorial, as we don't typically want to install jupyter, but
# clone it for reference.
. $check settings_repo geoips_tutorial $test_exit $install_script

# Private repos - only clone if GEOIPS_USE_PRIVATE_PLUGINS is set to "true"
if [[ "$GEOIPS_USE_PRIVATE_PLUGINS" == "true" ]]; then
    . $check source_repo geoips_wsfm $test_exit $install_script
    . $check source_repo ryglickicane $test_exit $install_script
    . $check source_repo tc_mint $test_exit $install_script
fi

. $check source_repo template_basic_plugin $test_exit $install_script

###########################################
# DO NOT alphabetize plugin packages in this section.
# Currently these need to be installed in this order, until the fortran pyproject.toml builds are working.
. $check source_repo fortran_utils $test_exit $install_script
. $check source_repo rayleigh $test_exit $install_script
. $check source_repo ancildat $test_exit $install_script
. $check source_repo synth_green $test_exit $install_script

# The above fortran packages need to be installed BEFORE installing geocolor, lunarref, or true_color.
. $check source_repo geocolor $test_exit $install_script

# Private repos (lunarref and true_color) - only clone if GEOIPS_USE_PRIVATE_PLUGINS is set to "true"
if [[ "$GEOIPS_USE_PRIVATE_PLUGINS" == "true" ]]; then
    . $check source_repo lunarref $test_exit $install_script
    . $check source_repo true_color $test_exit $install_script
    . $check source_repo geoips_debra $test_exit $install_script
    . $check source_repo geoips_nucaps $test_exit $install_script
    . $check source_repo pyrocb $test_exit $install_script
fi
###########################################

# Test data repos required for fully supported plugin packages (above)
# . $check run_command "geoips config install template_test_data"
. $check run_command "geoips config install test_data_clavrx"
. $check run_command "geoips config install test_data_fusion"
. $check run_command "geoips config install test_data_geocolor"
# Takes forever, skip
# geoips config install test_data_mint_analysis

# Private test data - only install if GEOIPS_USE_PRIVATE_PLUGINS is set to "true"
if [[ "$GEOIPS_USE_PRIVATE_PLUGINS" == "true" ]]; then
    . $check run_command "geoips config install test_data_mint"
    . $check run_command "geoips config install test_data_tomorrowio"
    . $check run_command "geoips config install test_data_wsfm"
fi

if [[ "$skip_create_registries" == "true" ]]; then
    echo "Skipping geoips config create-registries"
else
    . $check run_command "geoips config create-registries"
fi
