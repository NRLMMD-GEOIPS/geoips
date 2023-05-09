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
    git lfs install
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'git lfs install' failed, please install git lfs before proceeding"
        exit 1
    else
        echo ""
        echo "SUCCESS: 'git lfs install' appears to be installed successfully"
    fi 
fi

if [[ "$1" == "imagemagick" ]]; then
    compare --version
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'compare --version' failed, please install imagemagick before proceeding"
        exit 1
    else
        echo ""
        echo "SUCCESS: 'imagemagick' appears to be installed successfully"
    fi
fi

if [[ "$1" == "wget" ]]; then
    wget --version
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'wget --version' failed, please install wget before proceeding"
        exit 1
    else
        echo ""
        echo "SUCCESS: 'wget' appears to be installed successfully"
    fi
fi

if [[ "$1" == "git" ]]; then
    git --version
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'git --version' failed, please install git before proceeding"
        exit 1
    else
        echo ""
        echo "SUCCESS: 'git' appears to be installed successfully"
    fi
fi

if [[ "$1" == "openblas" ]]; then
    locate libopenblas.so
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'locate libopenblas.so' failed, please install openblas before proceeding"
        exit 1
    else
        echo ""
        echo "SUCCESS: 'openblas' appears to be installed successfully"
    fi
fi

if [[ "$1" == "libgeos" ]]; then
    locate libgeos.so
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'locate libgeos.so' failed, please install libgeos before proceeding"
        exit 1
    else
        echo ""
        echo "SUCCESS: 'libgeos' appears to be installed successfully"
    fi
fi

if [[ "$1" == "python" ]]; then
    python --version
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'python --version' failed, please install python >= 3.9 before proceeding"
        exit 1
    else
        echo ""
        echo "SUCCESS: 'python' appears to be installed successfully"
    fi
fi

if [[ "$1" == "rclone" ]]; then
    rclone --version
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
    fi
fi

if [[ "$1" == "cartopy" ]]; then
    python -c "import cartopy"
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'python -c 'import cartopy'' failed, please install cartopy before proceeding"
        exit 1
    else
        echo ""
        echo "SUCCESS: 'cartopy' appears to be installed successfully"
    fi
fi

if [[ "$1" == "matplotlib" ]]; then
    python -c "import matplotlib"
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

if [[ "$1" == "test_data_clavrx" ]]; then
    ls $GEOIPS_TESTDATA_DIR/test_data_clavrx/data/*
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'ls $GEOIPS_TESTDATA_DIR/test_data_clavrx/data/*' failed, going to install repo test_data_clavrx before proceeding"
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh setup_test_repo test_data_clavrx main
        exit 1
    else
        echo ""
        echo "SUCCESS: repo 'test_data_clavrx' appears to be installed successfully"
    fi
fi

if [[ "$1" == "test_data_amsr2" ]]; then
    ls $GEOIPS_TESTDATA_DIR/test_data_clavrx/data/*
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'ls $GEOIPS_TESTDATA_DIR/test_data_amsr2/data/*' failed, going to install repo test_data_amsr2 before proceeding"
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh setup_test_repo test_data_amsr2 main
        echo "test_data_amsr2 repo installed, please retry the corresponding test script which caused the previous error"
        exit 1
    else
        echo ""
        echo "SUCCESS: repo 'test_data_amsr2' appears to be installed successfully"
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
    fi
fi