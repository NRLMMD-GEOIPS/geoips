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
    ls $GEOIPS_TESTDATA_DIR/$test_repo/data/*.gz >& /dev/null
    retval_gz=$?
    ls $GEOIPS_TESTDATA_DIR/$test_repo/data/*.bz2 >& /dev/null
    retval_bz2=$?
    if [[ "$retval" != "0" ]]; then
        echo ""
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh setup_test_repo $test_repo main
        echo ""
        echo "WARNING: 'ls $GEOIPS_TESTDATA_DIR/$test_repo/data/*' initially failed."
        echo "    Installed repo $test_repo, please re-run test command. "
        if [[ "$exit_on_missing" == "true" ]]; then
            exit 1
        fi
    elif [[ "$retval_gz" == "0" || "$retval_bz2" == "0" ]]; then
        echo ""
        echo "WARNING: 'ls $GEOIPS_TESTDATA_DIR/$test_repo/data/*.gz/bz2/tgz' had data!"
        echo "    Uncompressing data in $test_repo."
        echo ""
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh setup_test_repo $test_repo main
        if [[ "$exit_on_missing" == "true" ]]; then
            echo "FAILED check on $test_repo."
            echo "    Uncompressed data in $test_repo, now please re-run test command."
            exit 1
        fi
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
        echo "WARNING: 'ls $GEOIPS_PACKAGES_DIR/$source_repo/*' failed."
        echo "    Installing repo $source_repo."
        echo ""
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh clone_source_repo $source_repo integration
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh install_geoips_plugin $source_repo
        if [[ "$exit_on_missing" == "true" ]]; then
            echo "FAILED check on $source_repo."
            echo "    Installed repo $source_repo, now please re-run test command."
            exit 1
        fi
    else
        echo ""
        echo "SUCCESS: repo '$source_repo' appears to be installed successfully"
        echo "    "`ls -ld $GEOIPS_PACKAGES_DIR/$source_repo`
    fi
fi

if [[ "$1" == "aws_data" ]]; then
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
        setup_command="setup_abi_test_data low_memory"
        test_data_path=$GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/goes16/20200918/1950
        test_data_files=$test_data_path/*.nc
    elif [[ "$data_type" == "fusion_data" ]]; then
        setup_command="setup_fusion_test_data"
        test_data_path=$GEOIPS_TESTDATA_DIR/test_data_fusion/data/himawari8_20210929.0000
        test_data_files=$test_data_path/*
    elif [[ "$data_type" == "ahi_terminator" ]]; then
        # ie, test_data_noaa_aws/data/himawari8/20220109/2000
        test_data_path=$GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/himawari8/20220109/2000
        test_data_files=$test_data_path/*
    fi

    # There *should* be files here
    ls $test_data_files >& /dev/null
    retval=$?
    # There should *not* be any bz2s
    ls $test_data_path/*.bz2 >& /dev/null
    retval_bz2=$?

    # If there weren't any files, may be a git lfs problem (or just not downloaded yet)
    if [[ "$retval" != "0" ]]; then
        echo ""
        echo "WARNING: 'ls $test_data_files' failed."
        echo "    Installing repo $data_type."
        echo ""
        $GEOIPS_PACKAGES_DIR/geoips/setup.sh $setup_command
        if [[ "$exit_on_missing" == "true" ]]; then
            echo "FAILED check on $data_type."
            echo "    Installed $data_type, now please re-run test command."
            exit 1
        fi
    # If there were bz2s, decompress them.
    elif [[ "$retval_bz2" == "0" ]]; then
        echo ""
        echo "WARNING: 'ls $test_data_bz2_path' had data!"
        echo "    Uncompressing data in $data_type."
        echo ""
        bunzip2 -f $test_data_bz2_path
        if [[ "$exit_on_missing" == "true" ]]; then
            echo "FAILED check on $data_type."
            echo "    Uncompressed data in $data_type, now please re-run test command."
            exit 1
        fi
    else
        echo ""
        echo "SUCCESS: repo '$data_type' appears to be installed successfully"
        ls -d $test_data_path
    fi
fi
