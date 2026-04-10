#!/bin/bash

# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

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

. $check geoips_base

# If you already have a .gitconfig, this won't do anything.
# Gives some reasonable defaults if you don't have one.
. $check set_gitconfig

. $check run_command "geoips config install test_data_amsr2"

if [[ "$skip_create_registries" == "true" ]]; then
    echo "Skipping pluginify create"
else
    pluginify create -n geoips.plugin_packages
fi
