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
if [[ "$5" != "" ]]; then
    test_script="$5"
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

if [[ "$1" == "test_repo" || "$1" == "source_repo" ]]; then
    repo_name=$2

    if [[ "$1" == "test_repo" ]]; then
        repo_name_string="tests data repo $repo_name"
        repo_dir=$GEOIPS_TESTDATA_DIR/$repo_name
        repo_url=$GEOIPS_REPO_URL/${repo_name}.git
        data_path="$repo_dir/data/*"
        gz_data_path="$repo_dir/data/*.gz"
        bz2_data_path="$repo_dir/data/*.bz2"
        uncompress_script=$GEOIPS_TESTDATA_DIR/$repo_name/uncompress_test_data.sh
    elif [[ "$1" == "source_repo" ]]; then
        repo_name_string="source repo $repo_name"
        repo_dir=$GEOIPS_PACKAGES_DIR/$repo_name
        repo_url=$GEOIPS_REPO_URL/${repo_name}.git
        data_path="$repo_dir/tests/*"
        gz_data_path="$repo_dir/tests/outputs/*/*.gz"
        bz2_data_path="$repo_dir/tests/outputs/*/*/*.gz"
        uncompress_script=$GEOIPS_PACKAGES_DIR/$repo_name/tests/uncompress_test_data.sh
    fi

    ls $data_path >> $install_log 2>&1
    retval=$?
    ls $gz_data_path >> $install_log 2>&1
    retval_gz=$?
    ls $bz2_data_path >> $install_log 2>&1
    retval_bz2=$?
    if [[ "$retval" != "0" ]]; then
        if [[ "$exit_on_missing" == "true" ]]; then
            echo "FAILED: Missing $repo_name_string"
            echo "        Please run install script, then rerun test script. "
            echo "        $install_script"
            echo "        $test_script"
            exit 1
        fi
        echo "Installing $repo_name_string .... "
        echo "  $repo_dir/"
        echo "git clone $repo_url $repo_dir" >> $install_log 2>&1
        git clone $repo_url $repo_dir >> $install_log 2>&1
        clone_retval=$?
        uncompress_retval=0
        if [[ -f $uncompress_script ]]; then
            echo "$uncompress_script" >> $install_log 2>&1
            $uncompress_script >> $install_log 2>&1
            uncompress_retval=$?
        fi
        pip_retval=0
        if [[ "$1" == "source_repo" ]]; then
            echo "pip install -e $repo_dir" >> $install_log 2>&1
            pip install -e $repo_dir >> $install_log 2>&1
            pip_retval=$?
        fi
        if [[ "$clone_retval" == "0" && "$uncompress_retval" == "0" && "$pip_retval" == "0" ]]; then
            echo "SUCCESS: Cloned, installed, and uncompressed $repo_name_string"
        else
            echo "FAILED: $repo_name_string clone, install, or uncompress returned non-zero"
            echo "        try deleting directory and re-running"
            exit 1
        fi
    elif [[ "$retval_gz" == "0" || "$retval_bz2" == "0" ]]; then
        if [[ "$exit_on_missing" == "true" ]]; then
            echo "FAILED: Compressed data still in $repo_name_string"
            echo "        Please run install script, then rerun test script. "
            echo "        $install_script"
            echo "        $test_script"
            exit 1
        fi
        echo "Uncompressing data in ${repo_name_string}."
        echo "  ls $repo_dir/data/*.gz/bz2/tgz"
        uncompress_retval=0
        if [[ -f $uncompress_script ]]; then
            echo "$uncompress_script" >> $install_log 2>&1
            $uncompress_script >> $install_log 2>&1
            uncompress_retval=$?
        fi
        if [[ "$uncompress_retval" == "0" ]]; then
            echo "SUCCESS: Uncompressed $repo_name_string"
        else
            echo "FAILED: $repo_name_string setup returned non-zero"
            echo "        try deleting directory and re-running"
            exit 1
        fi
    else
        echo "SUCCESS: $repo_name_string appears to be installed successfully"
        echo "    "`ls -ld $repo_dir`
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
            echo "        $test_script"
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
            echo "        $test_script"
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

if [[ "$1" == "ancillary_data" && "$2" == "cartopy_shapefiles" ]]; then
    if [[ -z "$CARTOPY_DATA_DIR" ]]; then
        echo "FAILED: cartopy_shapefiles requested and CARTOPY_DATA_DIR not set"
        echo "        please set \$CARTOPY_DATA_DIR to your desired location and retry"
        echo "If shapefiles do not already exist in \$CARTOPY_DATA_DIR:"
        echo "  1. shapefiles will be downloaded from:"
        echo "      git clone https://github.com/nvkelso/natural-earth-vector"
        echo "  2. shapefiles will be downloaded to:"
        echo "      \$CARTOPY_DATA_DIR/shapefiles_clone/natural-earth-vector"
        echo "  3. cloned shapefiles will be linked into location cartopy expects:"
        echo "      \$CARTOPY_DATA_DIR/shapefiles/natural_earth"
        exit 1
    fi
    clone_dir=$CARTOPY_DATA_DIR/shapefiles_clone/natural-earth-vector
    link_dir=$CARTOPY_DATA_DIR/shapefiles/natural_earth
    ls $link_dir/cultural/*.shp >> $install_log 2>&1
    retval=$?
    if [[ "$retval" == "0" ]]; then
        echo "SUCCESS: cartopy_shapefiles appear to be successfully installed"
        echo "         if you are having comparison errors, you can try"
        echo "         deleting the contents of \$CARTOPY_DATA_DIR, and"
        echo "         rerunning check_system_requirements.sh cartopy_shapefiles"
        ls -ld $link_dir/cultural
        ls -ld $link_dir/physical
    else
        if [[ "$exit_on_missing" == "true" ]]; then
            echo "FAILED: cartopy_shapefiles missing in $CARTOPY_DATA_DIR."
            echo "  expected files: $link_dir/cultural/*.shp"
            echo ""
            echo "  CARTOPY_DATA_DIR: $CARTOPY_DATA_DIR"
            echo "  "`ls -ld $CARTOPY_DATA_DIR`
            echo ""
            echo "  Please:"
            echo "    remove $CARTOPY_DATA_DIR if it exists:"
            echo "      # rm -rf $CARTOPY_DATA_DIR"
            echo "    then re-run install script:"
            echo "      $install_script"
            echo "    then re-run test script."
            echo "      $test_script"
            exit 1
        fi
        echo ""
        echo "Installing github.com/nvkelso/natural-earth-vector map data, "
        echo "  latest version, (last tested v5.2.0). This will take a while" >> $install_log 2>&1
        echo "    destination: $clone_dir" >> $install_log 2>&1
        mkdir -p $clone_dir
        git clone https://github.com/nvkelso/natural-earth-vector $clone_dir
        clone_retval=$?
        if [[ "$clone_retval" != "0" ]]; then
            echo "FAILED: 'cartopy_shapefiles' natural-earth-vector clone failed. Try again."
            echo "  May need to delete existing directory if it exists:"
            echo "    # rm -rf $clone_dir"
            exit 1
        fi
        git -C $clone_dir fetch --all --tags --prune >> $install_log 2>&1
        # Previously 5.0.0, 20220607 5.2.0
        # echo "    **Checking out tag v5.2.0, to ensure tests pass"
        # git checkout tags/v5.2.0
        git -C $clone_dir tag | tail -n 5 >> $install_log 2>&1
        echo "" >> $install_log 2>&1
        echo "**Linking natural-earth-data to $link_dir/cultural and physical" >> $install_log 2>&1
        mkdir -p $link_dir/cultural
        mkdir -p $link_dir/physical
        ln -sfv $clone_dir/*_cultural/*/* $link_dir/cultural >> $install_log 2>&1
        ln1_retval=$?
        ln -sfv $clone_dir/*_physical/*/* $link_dir/physical >> $install_log 2>&1
        ln2_retval=$?
        ln -sfv $clone_dir/*_cultural/* $link_dir/cultural >> $install_log 2>&1
        ln3_retval=$?
        ln -sfv $clone_dir/*_physical/* $link_dir/physical >> $install_log 2>&1
        ln4_retval=$?
        ls $link_dir/cultural/*.shp >> $install_log 2>&1
        ls_retval=$?
        if [[ $ln1_retval != 0 || $ln2_retval != 0 || $ln3_retval != 0 || $ln4_retval != 0 ]]; then
            echo "FAILED: You MUST be able to replace ALL user cartopy data with natural-earth-vector downloads!"
            echo "Please remove cartopy shapefiles and replace with cloned natural-earth-vector files"
            echo "  rm -fv $link_dir/cultural/*"
            echo "  rm -fv $link_dir/physical/*"
            echo "  ln -sfv $clone_dir/*_cultural/*/* $link_dir/cultural"
            echo "  ln -sfv $clone_dir/*_physical/*/* $link_dir/physical"
            echo "  ln -sfv $clone_dir/*_cultural/* $link_dir/cultural"
            echo "  ln -sfv $clone_dir/*_physical/* $link_dir/physical"
            exit 1
        elif [[ "$ls_retval" != "0" ]]; then
            echo "FAILED: cartopy_shapefiles missing in $CARTOPY_DATA_DIR."
            echo "  expected files: $link_dir/cultural/*.shp"
            echo ""
            echo "  CARTOPY_DATA_DIR: $CARTOPY_DATA_DIR"
            echo "  "`ls -ld $CARTOPY_DATA_DIR`
            echo ""
            echo "  Please:"
            echo "    remove $CARTOPY_DATA_DIR if it exists:"
            echo "      # rm -rf $CARTOPY_DATA_DIR"
            echo "    then re-run install script:"
            echo "      $install_script"
            echo "    then re-run test script."
            echo "      $test_script"
            exit 1
        else
            echo "SUCCESS: Installed shapefiles in \$CARTOPY_DATA_DIR."
            ls -ld $link_dir/cultural
            ls -ld $link_dir/physical
        fi
    fi
fi
