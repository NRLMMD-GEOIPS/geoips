#!/bin/bash

# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

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

. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh geoips_base

# If you already have a .gitconfig, this won't do anything.
# Gives some reasonable defaults if you don't have one.
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh set_gitconfig

geoips config install test_data_amsr2

if [[ "$skip_create_registries" == "true" ]]; then
    echo "Skipping geoips config create-registries"
else
    geoips config create-registries
fi
