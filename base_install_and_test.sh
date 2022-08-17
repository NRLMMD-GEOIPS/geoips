# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # # 
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # # 
# # # This program is free software:
# # # you can redistribute it and/or modify it under the terms
# # # of the NRLMMD License included with this program.
# # # 
# # # If you did not receive the license, see
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/
# # # for more information.
# # # 
# # # This program is distributed WITHOUT ANY WARRANTY;
# # # without even the implied warranty of MERCHANTABILITY
# # # or FITNESS FOR A PARTICULAR PURPOSE.
# # # See the included license for more details.

#!/bin/bash

check_continue() {
    unset CONTINUE
    while [ -z "$CONTINUE" ]; do
        echo ""
        echo ""
        echo "Just completed '$1'"
        echo "Y or y to perform '$2'"
        echo "K or k to skip '$2' but continue to following step"
        echo "Q or q to quit installation altogether?"
        read -r -p "[y/k/q]: " CONTINUE
    done
    if [[ $CONTINUE == "q" || $CONTINUE == "Q" ]]; then
        echo "Quitting"
        exit 1
    elif [[ $CONTINUE == "k" || $CONTINUE == "K" ]]; then
        echo "Skipping"
        skip_next="yes" 
    elif [[ $CONTINUE == "y" || $CONTINUE == "Y" ]]; then
        echo "Continuing!"
        skip_next="no"
    else
        echo "*********************************"
        echo "Please enter one of [y/k/q]"
        echo "*********************************"
        check_continue "$1" "$2"
    fi
}

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

    
if [[ "$GEOIPS_BASEDIR" == "" ]]; then
    echo "Must set GEOIPS_BASEDIR environment variable prior to installation"
    exit 1
fi

# This checks/sets required environment variables for setup - without requiring sourcing a geoips config in advance
. $GEOIPS_BASEDIR/geoips_packages/geoips/setup/repo_clone_update_install.sh setup

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
    echo "    GEOIPS_BASEDIR:       $GEOIPS_BASEDIR"
    echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
    echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
    echo "    which conda (should not exist yet): "`which conda`

check_continue "verifying GEOIPS_BASEDIR and GEOIPS_CONFIG_FILE and GEOIPS_ACTIVE_BRANCH" "update geoips repo to $GEOIPS_ACTIVE_BRANCH"

    if [[ "$skip_next" == "no" ]]; then
        date -u
        # Initial clone of geoips repo, to obtain setup scripts
        mkdir -p $GEOIPS_BASEDIR/geoips_packages
        git clone $GEOIPS_REPO_URL/geoips.git $GEOIPS_BASEDIR/geoips_packages/geoips
        
        git -C $GEOIPS_BASEDIR/geoips_packages/geoips pull
        git -C $GEOIPS_BASEDIR/geoips_packages/geoips checkout -t origin/$GEOIPS_ACTIVE_BRANCH
        git -C $GEOIPS_BASEDIR/geoips_packages/geoips checkout $GEOIPS_ACTIVE_BRANCH
        git -C $GEOIPS_BASEDIR/geoips_packages/geoips pull

        ls -ld $GEOIPS_BASEDIR/geoips_packages/*
        
        echo ""
        echo "Confirm environment variables point to desired installation parameters:"
        echo "    GEOIPS_BASEDIR:       $GEOIPS_BASEDIR"
        echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
        echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
        echo "    which conda (should not exist yet!): "`which conda`
        date -u
    fi

check_continue "updating geoips" "install conda"

    if [[ "$skip_next" == "no" ]]; then
        date -u
        # Install conda
        # Do not initialize your shell at the end, to allow switching between versions!!!
        $GEOIPS_BASEDIR/geoips_packages/geoips/setup.sh conda_install

        # Activate current conda base environment - note geoips_conda doesn't exist yet, but that is ok.
        # We need to at least point to "new" python and conda
        source $GEOIPS_CONFIG_FILE

        echo ""
        echo "Confirm environment variables point to desired installation parameters:"
        echo "    GEOIPS_BASEDIR:       $GEOIPS_BASEDIR"
        echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
        echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
        echo "    which conda (point to geoips_dependencies/miniconda3): "`which conda`
        date -u
    fi
    source ~/.bashrc
    env

check_continue "installing conda (should point to $GEOIPS_BASEDIR/geoips_dependencies/miniconda3)" "create geoips_conda_env"

    if [[ "$skip_next" == "no" ]]; then
        date -u
        # Create geoips conda environment
        $GEOIPS_BASEDIR/geoips_packages/geoips/setup.sh conda_update  # only for a fresh Miniconda install
        $GEOIPS_BASEDIR/geoips_packages/geoips/setup.sh create_geoips_conda_env
        # Now we can use source $GEOIPS_CONFIG_FILE
        source $GEOIPS_CONFIG_FILE
        echo ""
        echo "Confirm environment variables point to desired installation parameters:"
        echo "    GEOIPS_BASEDIR:       $GEOIPS_BASEDIR"
        echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
        echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
        echo "    which conda (should point to geoips_dependencies/bin): "`which conda`
        echo "    which pip (should point to miniconda3 envs/geoips_conda): "`which pip`
        echo "    which python (should point to miniconda3 envs/geoips_conda): "`which python`
        date -u
    fi

check_continue "creating geoips_conda_env (should point to $GEOIPS_BASEDIR/geoips_dependencies/miniconda3/envs/geoips_conda)" "install geoips and dependencies"

    if [[ "$skip_next" == "no" ]]; then
        date -u
        # Actually install geoips and all dependencies (cartopy, etc)
        source $GEOIPS_CONFIG_FILE
        $GEOIPS_BASEDIR/geoips_packages/geoips/setup.sh install $bandwidth_option
        echo ""
        echo "Confirm environment variables point to desired installation parameters:"
        echo "    GEOIPS_BASEDIR:       $GEOIPS_BASEDIR"
        echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
        echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
        echo "    which conda (should point to geoips_dependencies/bin): "`which conda`
        echo "    which python (should point to miniconda3 envs/geoips_conda): "`which python`
        date -u
    fi

# Only required to ensure shapefiles match for valid cartopy-based test outputs
# Not required if:
#   1. We recently updated the test repo outputs to use the latest shapefiles
#   2. We are comparing test outputs that do *not* incorporate cartopy-based coastlines, gridlines, etc
# Currently assuming test outputs are up-to-date with the latest shapefiles (updated June 2022)
## check_continue "install geoips and dependencies" "Download cartopy natural earth data (REQUIRED for successful test returns, but takes ~10min and ~16GB to download)"
## 
##     if [[ "$skip_next" == "no" ]]; then
## 
##         source $GEOIPS_CONFIG_FILE
##         $GEOIPS_BASEDIR/geoips_packages/geoips/setup.sh download_cartopy_natural_earth
## 
##         echo ""
##         echo "Confirm environment variables point to desired installation parameters:"
##         echo "    GEOIPS_BASEDIR:       $GEOIPS_BASEDIR"
##         echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
##         echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
##         echo "    which conda (should point to geoips_dependencies/bin): "`which conda`
##         echo "    which python (should point to miniconda3 envs/geoips_conda): "`which python`
##     fi

# NOTE: This was previously required when cartopy had ~/.local hardcoded in as the primary location to search for shapefiles
#   https://scitools.org.uk/cartopy/docs/latest/reference/config.html
# As of August 6, 2021, you can set CARTOPY_DATA_DIR and it will look there for shapefiles, so we will not have to do
#   the hokey linking to ~/.local anyway!!
#   https://github.com/SciTools/cartopy/commit/300b8c32d411c25b6c2d2ca3bc73794761fb932b
## check_continue "Downloading cartopy natural earth data" "Link cartopy natural earth data to ~/.local/share/cartopy (to ensure cartopy uses the correct shapefiles in order for test outputs to match exactly)"
## 
##     if [[ "$skip_next" == "no" ]]; then
##         source $GEOIPS_CONFIG_FILE
##         $GEOIPS_BASEDIR/geoips_packages/geoips/setup.sh link_cartopy_natural_earth
## 
##         echo ""
##         echo "Confirm environment variables point to desired installation parameters:"
##         echo "    GEOIPS_BASEDIR:       $GEOIPS_BASEDIR"
##         echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
##         echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
##         echo "    which conda (should point to geoips_dependencies/bin): "`which conda`
##         echo "    which python (should point to miniconda3 envs/geoips_conda): "`which python`
##     fi

check_continue "installing geoips dependencies" "install rclone (REQUIRED for test script)"
    if [[ "$skip_next" == "no" ]]; then
        date -u
        source $GEOIPS_CONFIG_FILE
        $GEOIPS/setup.sh setup_rclone # abi/ahi ingest
        echo ""
        echo "Confirm environment variables point to desired installation parameters:"
        echo "    GEOIPS_BASEDIR:       $GEOIPS_BASEDIR"
        echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
        echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
        echo "    which conda (should point geoips_dependencies/bin): "`which conda`
        echo "    which python (should point to miniconda3 envs/geoips_conda): "`which python`
        date -u
    fi

## check_continue "installing rclone" "OPTIONAL install seviri libraries (required for seviri HRIT processing)"
##     if [[ "$skip_next" == "no" ]]; then
##         source $GEOIPS_CONFIG_FILE
##         $GEOIPS/setup.sh setup_seviri
##         echo ""
##         echo "Confirm environment variables point to desired installation parameters:"
##         echo "    GEOIPS_BASEDIR:       $GEOIPS_BASEDIR"
##         echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
##         echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
##         echo "    which conda (should point geoips_dependencies/bin): "`which conda`
##         echo "    which python (should point to miniconda3 envs/geoips_conda): "`which python`
##     fi

## check_continue "installing seviri libraries" "OPTIONAL install vim8"
## 
##     if [[ "$skip_next" == "no" ]]; then
##         source $GEOIPS_CONFIG_FILE
##         $GEOIPS/setup.sh setup_vim8  # vim syntax highlighting
## 
##         echo ""
##         echo "Confirm environment variables point to desired installation parameters:"
##         echo "    GEOIPS_BASEDIR:       $GEOIPS_BASEDIR"
##         echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
##         echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
##         echo "    which conda (should point geoips_dependencies/bin): "`which conda`
##         echo "    which python (should point to miniconda3 envs/geoips_conda): "`which python`
##     fi

## check_continue "installing vim8" "OPTIONAL install vim8 plugins (updates ~/.vim and ~/.vimrc to set up syntax highlighting based on geoips style guide)"
## 
##     if [[ "$skip_next" == "no" ]]; then
##         source $GEOIPS_CONFIG_FILE
##         $GEOIPS/setup.sh setup_vim8_plugins  # vim syntax highlighting
## 
##         echo ""
##         echo "Confirm environment variables point to desired installation parameters:"
##         echo "    GEOIPS_BASEDIR:       $GEOIPS_BASEDIR"
##         echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
##         echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
##         echo "    which conda (should point geoips_dependencies/bin): "`which conda`
##         echo "    which python (should point to miniconda3 envs/geoips_conda): "`which python`
##     fi

check_continue "installing geoips, cartopy data, dependencies, and external packages" "run basic test script"

    if [[ "$skip_next" == "no" ]]; then
        date -u
        source $GEOIPS_CONFIG_FILE
        $GEOIPS_BASEDIR/geoips_packages/geoips/setup.sh setup_abi_test_data $bandwidth_option
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
        echo "    GEOIPS_BASEDIR:       $GEOIPS_BASEDIR"
        echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
        echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
        echo "    which conda (should point geoips_dependencies/bin): "`which conda`
        echo "    which python (should point to miniconda3 envs/geoips_conda): "`which python`
        date -u
    fi

check_continue "Installing and testing geoips" "Obtain amsr2 test data repository"

    if [[ "$skip_next" == "no" ]]; then
        date -u
        source $GEOIPS_CONFIG_FILE
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh clone_test_repo test_data_amsr2
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh update_test_repo test_data_amsr2 $GEOIPS_ACTIVE_BRANCH
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh uncompress_test_data test_data_amsr2
        date -u
    fi

check_continue "Obtaining amsr2 test data repository" "Running AMSR2 tests"

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
echo "    GEOIPS_BASEDIR:       $GEOIPS_BASEDIR"
echo "    GEOIPS_CONFIG_FILE:   $GEOIPS_CONFIG_FILE"
echo "    GEOIPS_ACTIVE_BRANCH: $GEOIPS_ACTIVE_BRANCH"
echo "    which conda (should point geoips_dependencies/bin): "`which conda`
echo "    which python (should point to miniconda3 envs/geoips_conda): "`which python`
check_continue "Installing and testing geoips" "Done with base installation and test!"
