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

if [[ "$1" == "gitlfs" ]]; then
    git lfs install >& /dev/null
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'git lfs install' failed, please install git lfs before proceeding"
        exit 1
    else
        echo ""
        echo "SUCCESS: 'git lfs install' appears to be installed successfully"
        echo "    "`which git`
    fi 
fi

if [[ "$1" == "imagemagick" ]]; then
    compare --version >& /dev/null
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'compare --version' failed, please install imagemagick before proceeding"
        exit 1
    else
        echo ""
        echo "SUCCESS: 'imagemagick' appears to be installed successfully"
        echo "    "`which compare`
    fi
fi

if [[ "$1" == "wget" ]]; then
    wget --version >& /dev/null
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'wget --version' failed, please install wget before proceeding"
        exit 1
    else
        echo ""
        echo "SUCCESS: 'wget' appears to be installed successfully"
        echo "    "`which wget`
    fi
fi

if [[ "$1" == "git" ]]; then
    git --version >& /dev/null
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'git --version' failed, please install git before proceeding"
        exit 1
    else
        echo ""
        echo "SUCCESS: 'git' appears to be installed successfully"
        echo "    "`which git`
    fi
fi

if [[ "$1" == "python" ]]; then
    python --version >& /dev/null
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'python --version' failed, please install python >= 3.9 before proceeding"
        exit 1
    else
        echo ""
        echo "SUCCESS: 'python' appears to be installed successfully"
        echo "    "`which python`
    fi
fi

if [[ "$1" == "rclone" ]]; then
    rclone --version >& /dev/null
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'rclone --version' failed, going to install install rclone before proceeding"
        source $GEOIPS_CONFIG_FILE
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh install $bandwidth_option
        exit 1
    else
        echo ""
        echo "SUCCESS: 'rclone' appears to be installed successfully"
        echo "    "`which rclone`
    fi
fi

if [[ "$1" == "cartopy" || "$1" == "libgeos" ]]; then
    python -c "import cartopy" >& /dev/null
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'python -c 'import cartopy'' failed, please install cartopy before proceeding"
        exit 1
    else
        echo ""
        echo "SUCCESS: 'cartopy/libgeos' appear to be installed successfully"
    fi
fi

if [[ "$1" == "scipy" || "$1" == "openblas" ]]; then
    python -c "import scipy" >& /dev/null
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'python -c 'import scipy'' failed, please install openblas/scipy before proceeding"
        exit 1
    else
        echo ""
        echo "SUCCESS: 'scipy/openblas' appear to be installed successfully"
    fi
fi

if [[ "$1" == "matplotlib" ]]; then
    python -c "import matplotlib" >& /dev/null
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'python -c 'import matplotlib'' failed, please install matplotlib before proceeding"
        exit 1
    else
        echo ""
        echo "SUCCESS: 'matplotlib' appears to be installed successfully"
    fi
fi

if [[ "$1" == "test_repo" ]]; then
    test_repo=$2
    ls $GEOIPS_TESTDATA_DIR/$test_repo/data/* >& /dev/null
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'ls $GEOIPS_TESTDATA_DIR/$test_repo/data/*' failed"
        echo "    going to install repo $test_repo before proceeding"
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh setup_test_repo $test_repo main
        exit 1
    else
        echo ""
        echo "SUCCESS: repo '$test_repo' appears to be installed successfully"
        echo "    "`ls -ld $GEOIPS_TESTDATA_DIR/$test_repo`
    fi
fi

if [[ "$1" == "source_repo" ]]; then
    source_repo=$2
    ls $GEOIPS_PACKAGES_DIR/$source_repo/* >& /dev/null
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'ls $GEOIPS_PACKAGES_DIR/$source_repo/*' failed"
        echo "going to install repo $source_repo before proceeding"
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh clone_source_repo $source_repo integration
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh install_geoips_plugin $source_repo
        exit 1
    else
        echo ""
        echo "SUCCESS: repo '$source_repo' appears to be installed successfully"
        echo "    "`ls -ld $GEOIPS_PACKAGES_DIR/$source_repo`
    fi
fi

if [[ "$1" == "test_data_abi_day" ]]; then
    ls $GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/*
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'ls $GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/*' failed, going to install repo test_data_abi_day before proceeding"
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh setup_abi_test_data
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh setup_abi_test_data low_memory
        exit 1
    else
        echo ""
        echo "SUCCESS: repo 'test_data_abi_day' appears to be installed successfully"
        echo "    "`ls -ld $GEOIPS_TESTDATA_DIR/test_data_noaa_aws`
    fi
fi
