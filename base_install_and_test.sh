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

source $GEOIPS_PACKAGES_DIR/geoips/setup/bash_setup/check_continue

if [[ "$1" == "" ]]; then
    GEOIPS_ACTIVE_BRANCH=main
else
    GEOIPS_ACTIVE_BRANCH=$1
fi

if [[ "$2" == "" ]]; then
    memory_option="high_memory"
else
    memory_option="low_memory"
fi

if [[ "$3" == "" ]]; then
    bandwidth_option="high_bandwidth"
else
    bandwidth_option="low_bandwidth"
fi

if [[ "$4" == "conda_defaults_channel" ]]; then
    conda_channel="conda_defaults_channel"
else
    conda_channel="conda-forge"
fi

if [[ "$GEOIPS_PACKAGES_DIR" == "" ]]; then
    echo "Must set GEOIPS_PACKAGES_DIR environment variable prior to installation"
    exit 1
fi

# This checks/sets required environment variables for setup - without requiring sourcing a geoips config in advance
. $GEOIPS_PACKAGES_DIR/geoips/setup/repo_clone_update_install.sh setup

    echo ""
    echo "NOTE Approximately 30GB disk space / 10GB memory required for complete installation and test"
    echo ""
    echo "NOTE Expert users can install piece meal to avoid this time consuming installation process (>1h)"
    echo "     This full installation installs ALL dependencies from scratch,"
    echo "     to ensure a consistent environment for successful test returns"
    echo "     This includes"
    echo "          * Full Miniconda installation"
    echo "          * full cartopy coastline and political borders information"
    echo "          * ABI test datasets"
    echo "          * vim8 installation with syntax highlighting to encourage following style guide"
    echo ""
    echo "Confirm environment variables point to desired installation parameters:"
    echo "    GEOIPS_PACKAGES_DIR:  $GEOIPS_PACKAGES_DIR"
    echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
    echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
    echo "    which conda (should not exist yet): "`which conda`

check_continue "update geoips repo to $GEOIPS_ACTIVE_BRANCH"

    if [[ "$skip_next" == "no" ]]; then
        date -u
        # Initial clone of geoips repo, to obtain setup scripts
        mkdir -p $GEOIPS_PACKAGES_DIR
        git clone $GEOIPS_REPO_URL/geoips.git $GEOIPS_PACKAGES_DIR/geoips

        git -C $GEOIPS_PACKAGES_DIR/geoips pull
        git -C $GEOIPS_PACKAGES_DIR/geoips checkout -t origin/$GEOIPS_ACTIVE_BRANCH
        git -C $GEOIPS_PACKAGES_DIR/geoips checkout $GEOIPS_ACTIVE_BRANCH
        git -C $GEOIPS_PACKAGES_DIR/geoips pull

        ls -ld $GEOIPS_PACKAGES_DIR/*

        echo ""
        echo "Confirm environment variables point to desired installation parameters:"
        echo "    GEOIPS_PACKAGES_DIR:  $GEOIPS_PACKAGES_DIR"
        echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
        echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
        echo "    which conda (should not exist yet!): "`which conda`
        date -u
    fi

check_continue "install conda with $conda_channel"

    if [[ "$skip_next" == "no" ]]; then
        date -u
        # Install conda
        # Do not initialize your shell at the end, to allow switching between versions!!!
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh conda_install $conda_channel

        # Activate current conda base environment - note geoips_conda doesn't exist yet, but that is ok.
        # We need to at least point to "new" python and conda
        source $GEOIPS_CONFIG_FILE

        echo ""
        echo "Confirm environment variables point to desired installation parameters:"
        echo "    GEOIPS_PACKAGES_DIR:  $GEOIPS_PACKAGES_DIR"
        echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
        echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
        echo "    which conda (point to geoips_dependencies/miniconda3): "`which conda`
        date -u
    fi
    source ~/.bashrc
    env

check_continue "update conda with $conda_channel"

    if [[ "$skip_next" == "no" ]]; then
        date -u
        # Create geoips conda environment
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh conda_update $conda_channel # only for a fresh Miniconda install
        # Now we can use source $GEOIPS_CONFIG_FILE
        source $GEOIPS_CONFIG_FILE
        echo ""
        echo "Confirm environment variables point to desired installation parameters:"
        echo "    GEOIPS_PACKAGES_DIR:  $GEOIPS_PACKAGES_DIR"
        echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
        echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
        echo "    which conda (should point to geoips_dependencies/bin): "`which conda`
        echo "    which pip (should point to miniconda3 envs/geoips_conda): "`which pip`
        echo "    which python (should point to miniconda3 envs/geoips_conda): "`which python`
        date -u
    fi

check_continue "create geoips_conda_env with $conda_channel"

    if [[ "$skip_next" == "no" ]]; then
        date -u
        # Create geoips conda environment
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh create_geoips_conda_env $conda_channel
        # Now we can use source $GEOIPS_CONFIG_FILE
        source $GEOIPS_CONFIG_FILE
        echo ""
        echo "Confirm environment variables point to desired installation parameters:"
        echo "    GEOIPS_PACKAGES_DIR:  $GEOIPS_PACKAGES_DIR"
        echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
        echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
        echo "    which conda (should point to geoips_dependencies/bin): "`which conda`
        echo "    which pip (should point to miniconda3 envs/geoips_conda): "`which pip`
        echo "    which python (should point to miniconda3 envs/geoips_conda): "`which python`
        date -u
    fi

check_continue "install geoips and dependencies"

    if [[ "$skip_next" == "no" ]]; then
        date -u
        # Actually install geoips and all dependencies (cartopy, etc)
        source $GEOIPS_CONFIG_FILE
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh install $bandwidth_option
        echo ""
        echo "Confirm environment variables point to desired installation parameters:"
        echo "    GEOIPS_PACKAGES_DIR:  $GEOIPS_PACKAGES_DIR"
        echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
        echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
        echo "    which conda (should point to geoips_dependencies/bin): "`which conda`
        echo "    which python (should point to miniconda3 envs/geoips_conda): "`which python`
        date -u
    fi

check_continue "install rclone (REQUIRED for test script)"
    if [[ "$skip_next" == "no" ]]; then
        date -u
        source $GEOIPS_CONFIG_FILE
        $GEOIPS/setup.sh setup_rclone # abi/ahi ingest
        echo ""
        echo "Confirm environment variables point to desired installation parameters:"
        echo "    GEOIPS_PACKAGES_DIR:  $GEOIPS_PACKAGES_DIR"
        echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
        echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
        echo "    which conda (should point geoips_dependencies/bin): "`which conda`
        echo "    which python (should point to miniconda3 envs/geoips_conda): "`which python`
        date -u
    fi

check_continue "run basic test script"

    if [[ "$skip_next" == "no" ]]; then
        date -u
        source $GEOIPS_CONFIG_FILE
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh setup_abi_test_data $bandwidth_option
        if [[ "$memory_option" == "low_memory" ]]; then
            $GEOIPS/tests/test_base_install_low_memory.sh
        else
            $GEOIPS/tests/test_base_install.sh
        fi
        retval=$?

        echo ""
        echo "full return: $retval"
        echo ""
        echo "Confirm environment variables pointed to desired installation parameters:"
        echo "    GEOIPS_PACKAGES_DIR:  $GEOIPS_PACKAGES_DIR"
        echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
        echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
        echo "    which conda (should point geoips_dependencies/bin): "`which conda`
        echo "    which python (should point to miniconda3 envs/geoips_conda): "`which python`
        date -u
    fi

check_continue "Obtain amsr2 test data repository"

    if [[ "$skip_next" == "no" ]]; then
        date -u
        source $GEOIPS_CONFIG_FILE
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh clone_test_repo test_data_amsr2
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh update_test_repo test_data_amsr2 $GEOIPS_ACTIVE_BRANCH
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh uncompress_test_data test_data_amsr2
        date -u
    fi

check_continue "Running AMSR2 tests"

    if [[ "$skip_next" == "no" ]]; then
        date -u
        source $GEOIPS_CONFIG_FILE
        if [[ "$memory_option" == "low_memory" ]]; then
            $GEOIPS_PACKAGES_DIR/geoips/tests/scripts/amsr2.config_based_overlay_output_low_memory.sh
        else
            $GEOIPS_PACKAGES_DIR/geoips/tests/scripts/amsr2.config_based_overlay_output.sh
        fi
        date -u
    fi

echo "Confirm environment variables pointed to desired installation parameters:"
echo "    GEOIPS_PACKAGES_DIR:  $GEOIPS_PACKAGES_DIR"
echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
echo "    which conda (should point geoips_dependencies/bin): "`which conda`
echo "    which python (should point to miniconda3 envs/geoips_conda): "`which python`
check_continue "Installing and testing geoips" "Done with base installation and test!"
