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

exit_on_missing="false"
if [[ "$3" == "exit_on_missing" ]]; then
    exit_on_missing="true"
fi
if [[ "$4" != "" ]]; then
    install_script="$4"
fi

if [[ -z "$GEOIPS_OUTDIRS" || \
      -z "$GEOIPS_PACKAGES_DIR" || \
      -z "$GEOIPS_REPO_URL" || \
      -z "$GEOIPS_TESTDATA_DIR" ]]; then
    echo "Must define appropriate GEOIPS environment variables prior to using geoips:"
    echo "    GEOIPS_OUTDIRS       # Required for ALL geoips processing"
    echo "    GEOIPS_PACKAGES_DIR  # Required for integration testing"
    echo "    GEOIPS_REPO_URL      # Required for installation"
    echo "    GEOIPS_TESTDATA_DIR  # Required for integration testsing"
    exit 1
fi

install_log=$GEOIPS_OUTDIRS/logs/`date -u +%Y%m%d.%H%M%S`_install.log
mkdir -p `dirname $install_log`
echo ""
echo "Install log: $install_log"

if [[ "$1" == "gitlfs" ]]; then
    git lfs install >> $install_log 2>&1
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo "WARNING: 'git lfs install' failed, please install git lfs before proceeding"
        exit 1
    else
        echo "SUCCESS: 'git lfs install' appears to be installed successfully"
        echo "    "`which git`
    fi
fi

if [[ "$1" == "geoips_base" ]]; then
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh gitlfs
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh imagemagick
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh wget
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh git
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh python
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh openblas
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh libgeos
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh rclone
fi

if [[ "$1" == "imagemagick" ]]; then
    compare --version >> $install_log 2>&1
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo "WARNING: 'compare --version' failed, please install imagemagick before proceeding"
        exit 1
    else
        echo "SUCCESS: 'imagemagick' appears to be installed successfully"
        echo "    "`which compare`
    fi
fi

if [[ "$1" == "wget" ]]; then
    wget --version >> $install_log 2>&1
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo "WARNING: 'wget --version' failed, please install wget before proceeding"
        exit 1
    else
        echo "SUCCESS: 'wget' appears to be installed successfully"
        echo "    "`which wget`
    fi
fi

if [[ "$1" == "git" ]]; then
    git --version >> $install_log 2>&1
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo "WARNING: 'git --version' failed, please install git before proceeding"
        exit 1
    else
        echo "SUCCESS: 'git' appears to be installed successfully"
        echo "    "`which git`
    fi
fi

if [[ "$1" == "python" ]]; then
    python --version >> $install_log 2>&1
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo "WARNING: 'python --version' failed, please install python >= 3.9 before proceeding"
        exit 1
    else
        echo "SUCCESS: 'python' appears to be installed successfully"
        echo "    "`which python`
    fi
fi

if [[ "$1" == "rclone" ]]; then
    rclone --version >> $install_log 2>&1
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo "WARNING: 'rclone --version' failed, going to install install rclone before proceeding"
        source $GEOIPS_CONFIG_FILE
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh install $bandwidth_option
        exit 1
    else
        echo "SUCCESS: 'rclone' appears to be installed successfully"
        echo "    "`which rclone`
    fi
fi

if [[ "$1" == "cartopy" || "$1" == "libgeos" ]]; then
    python -c "import cartopy" >> $install_log 2>&1
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo "WARNING: 'python -c 'import cartopy'' failed, please install cartopy before proceeding"
        exit 1
    else
        echo "SUCCESS: 'cartopy/libgeos' appear to be installed successfully"
    fi
fi

if [[ "$1" == "scipy" || "$1" == "openblas" ]]; then
    python -c "import scipy" >> $install_log 2>&1
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo "WARNING: 'python -c 'import scipy'' failed, please install openblas/scipy before proceeding"
        exit 1
    else
        echo "SUCCESS: 'scipy/openblas' appear to be installed successfully"
    fi
fi

if [[ "$1" == "matplotlib" ]]; then
    python -c "import matplotlib" >> $install_log 2>&1
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo "WARNING: 'python -c 'import matplotlib'' failed, please install matplotlib before proceeding"
        exit 1
    else
        echo "SUCCESS: 'matplotlib' appears to be installed successfully"
    fi
fi

if [[ "$1" == "test_repo" ]]; then
    test_repo=$2
    ls $GEOIPS_TESTDATA_DIR/$test_repo/data/* >> $install_log 2>&1
    retval=$?
    ls $GEOIPS_TESTDATA_DIR/$test_repo/data/*.gz >> $install_log 2>&1
    retval_gz=$?
    ls $GEOIPS_TESTDATA_DIR/$test_repo/data/*.bz2 >> $install_log 2>&1
    retval_bz2=$?
    if [[ "$retval" != "0" ]]; then
        if [[ "$exit_on_missing" == "true" ]]; then
            echo "FAILED: Missing test data repo $test_repo"
            echo "        Please run install script, then rerun test script. "
            echo "        $install_script"
            exit 1
        fi
        echo "Installing test data repo $test_repo.... "
        echo "  $GEOIPS_TESTDATA_DIR/$test_repo/"
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh clone_test_repo $test_repo >> $install_log 2>&1
        clone_retval=$?
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh uncompress_test_data $test_repo >> $install_log 2>&1
        uncompress_retval=$?
        if [[ "$clone_retval" == "0" || "$uncompress_retval" == "0" ]]; then
            echo "SUCCESS: Cloned and uncompressed test data repo $test_repo"
        else
            echo "FAILED: test data repo $data_type clone or uncompress returned non-zero"
            echo "        try deleting directory and re-running"
            exit 1
        fi
    elif [[ "$retval_gz" == "0" || "$retval_bz2" == "0" ]]; then
        if [[ "$exit_on_missing" == "true" ]]; then
            echo "FAILED: Compressed data still in test data repo $test_repo"
            echo "        Please run install script, then rerun test script. "
            echo "        $install_script"
            exit 1
        fi
        echo "Uncompressing data in test data repo $test_repo."
        echo "  ls $GEOIPS_TESTDATA_DIR/$test_repo/data/*.gz/bz2/tgz"
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh uncompress_test_data $test_repo >> $install_log 2>&1
        uncompress_retval=$?
        if [[ "$clone_retval" == "0" && "$uncompress_retval" == "0" ]]; then
            echo "SUCCESS: Uncompressed test data repo $test_repo"
        else
            echo "FAILED: test data repo $data_type setup returned non-zero"
            echo "        try deleting directory and re-running"
            exit 1
        fi
    else
        echo "SUCCESS: test data repo '$test_repo' appears to be installed successfully"
        echo "    "`ls -ld $GEOIPS_TESTDATA_DIR/$test_repo`
    fi
fi

if [[ "$1" == "source_repo" ]]; then
    source_repo=$2
    ls $GEOIPS_PACKAGES_DIR/$source_repo/tests/* >> $install_log 2>&1
    retval=$?
    if [[ "$retval" != "0" ]]; then
        if [[ "$exit_on_missing" == "true" ]]; then
            echo "FAILED: Missing source repo $source_repo"
            echo "        Please run install script, then rerun test script. "
            echo "        $install_script"
            exit 1
        fi
        echo "Installing source repo $source_repo...."
        echo "  $GEOIPS_PACKAGES_DIR/$source_repo/"
        echo "$GEOIPS_PACKAGES_DIR/geoips/setup.sh install_geoips_plugin $source_repo" >> $install_log 2>&1
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh install_geoips_plugin $source_repo >> $install_log 2>&1
        if [[ "$?" == "0" ]]; then
            echo "SUCCESS: Installed source repo $source_repo"
        else
            echo "FAILED: source repo $source_repo clone or install returned non-zero"
            echo "        try deleting directory and re-running"
            exit 1
        fi
    else
        echo "SUCCESS: source repo '$source_repo' appears to be installed successfully"
        echo "    "`ls -ld $GEOIPS_PACKAGES_DIR/$source_repo`
    fi
fi

if [[ "$1" == "aws_test_data" ]]; then
    data_type=$2

    if [[ "$data_type" == "ahi_day" ]]; then
        setup_command=setup_ahi_test_data
        # ie, test_data_noaa_aws/data/himawari8/20200405/0000
        test_data_path=$GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/himawari8/20200405/0000
        test_data_files=$test_data_path/*
    elif [[ "$data_type" == "abi_day" ]]; then
        setup_command=setup_abi_test_data
        # ie test_data_noaa_aws/data/goes16/20200918/1950/OR_ABI*.nc
        test_data_path=$GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/goes16/20200918/1950
        test_data_files=$test_data_path/*C02*.nc
    elif [[ "$data_type" == "abi_day_low_memory" ]]; then
        setup_command="setup_abi_test_data low_bandwidth"
        test_data_path=$GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/goes16/20200918/1950
        test_data_files=$test_data_path/*C14*.nc
    elif [[ "$data_type" == "fusion_data" ]]; then
        setup_command="setup_fusion_test_data"
        test_data_path=$GEOIPS_TESTDATA_DIR/test_data_fusion/data/himawari8_20210929.0000
        test_data_files=$test_data_path/*
    elif [[ "$data_type" == "ahi_terminator" ]]; then
        setup_command="setup_ahi_test_data terminator"
        # ie, test_data_noaa_aws/data/himawari8/20220109/2000
        test_data_path=$GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/himawari8/20220109/2000
        test_data_files=$test_data_path/*
    fi

    # There *should* be files here
    ls $test_data_files >> $install_log 2>&1
    retval=$?
    # There should *not* be any bz2s
    ls $test_data_path/*.bz2 >> $install_log 2>&1
    retval_bz2=$?

    # If there weren't any files, may be a git lfs problem (or just not downloaded yet)
    if [[ "$retval" != "0" ]]; then
        if [[ "$exit_on_missing" == "true" ]]; then
            echo "FAILED: Missing aws test data $data_type"
            echo "        Please run install script, then rerun test script. "
            echo "        $install_script"
            exit 1
        fi
        echo "Installing aws test data $data_type...."
        echo "  $test_data_files"
        echo "$GEOIPS_PACKAGES_DIR/geoips/setup.sh $setup_command" >> $install_log 2>&1
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh $setup_command >> $install_log 2>&1
        if [[ "$?" == "0" ]]; then
            echo "SUCCESS: Installed aws test data $data_type."
        else
            echo "FAILED: aws test data $data_type setup returned non-zero"
            echo "        try deleting directory and re-running"
            exit 1
        fi
    # If there were bz2s, decompress them.
    elif [[ "$retval_bz2" == "0" ]]; then
        if [[ "$exit_on_missing" == "true" ]]; then
            echo "FAILED: Compressed aws test data $data_type still exists."
            echo "        Please run install script, then rerun test script. "
            echo "        $install_script"
            exit 1
        fi
        echo "Uncompressing data in aws test data $data_type...."
        echo "    $test_data_bz2_path"
        echo "bunzip2 -f $test_data_bz2_path" >> $install_log 2>&1
        bunzip2 -f $test_data_bz2_path >& install_log
        if [[ "$?" == "0" ]]; then
            echo "SUCCESS: Uncompressed data in aws test data $data_type."
        else
            echo "FAILED: Uncompress on aws test data $data_type returned non-zero"
            echo "        try deleting directory and re-running"
            exit 1
        fi
    else
        echo "SUCCESS: aws test data '$data_type' appears to be installed successfully"
        echo "    "`ls -ld $test_data_path`
    fi
fi
