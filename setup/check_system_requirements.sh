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

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

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

# These are the download locations used by the test_data function
test_data_urls=(
    "https://io.cira.colostate.edu/s/mQ2HbE2Js4E9rba/download/test_data_viirs.tgz"
    "https://io.cira.colostate.edu/s/CezXWwXg4qR2b94/download/test_data_smap.tgz"
    "https://io.cira.colostate.edu/s/HyHLZ9F8bnfcTcd/download/test_data_scat.tgz"
    "https://io.cira.colostate.edu/s/snxx8S5sQL3AL7f/download/test_data_sar.tgz"
    "https://io.cira.colostate.edu/s/fkiPS3jyrQGqgPN/download/test_data_noaa_aws.tgz"
    "https://io.cira.colostate.edu/s/LT92NiFSA8ZSNDP/download/test_data_gpm.tgz"
    "https://io.cira.colostate.edu/s/DSz2nZsiPMDeLEP/download/test_data_fusion.tgz"
    "https://io.cira.colostate.edu/s/ACLKdS2Cpgd2qkc/download/test_data_clarvx.tgz"
    "https://io.cira.colostate.edu/s/FmWwX2ft7KDQ8N9/download/test_data_amsr2.tgz"
)

# Requirements to run base geoips tests
if [[ "$1" == "geoips_base" ]]; then
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh imagemagick
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh git
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh python
fi

# Requirements to run the full suite of open source geoips tests
if [[ "$1" == "geoips_full" ]]; then
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh geoips_base
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh gcc
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh g++
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh openblas
fi

# Required for image comparisons
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

# Required for using the -C option since some people apparently have git older than
# 1.8.5 which was released in November 2013.
#
# Consider adding a version test here rather than requiring git to be installed in every
# conda environment.
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

# Consider adding a version test here rather than just allowing any python version.
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

# Needed for building akima. If we can build a distributable wheel for akima, then maybe
# we won't need this.
if [[ "$1" == "gcc" ]]; then
    gcc --version >> $install_log 2>&1
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo "WARNING: 'gcc --version' failed, please install gcc before proceeding"
        exit 1
    else
        echo "SUCCESS: 'gcc' appears to be installed successfully"
        echo "    "`which gcc`
    fi
fi

# Needed for building akima. If we can build a distributable wheel for akima, then maybe
# we won't need this.
if [[ "$1" == "g++" ]]; then
    g++ --version >> $install_log 2>&1
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo "WARNING: 'g++ --version' failed, pleas install g++ before proceeding"
        exit 1
    else
        echo "SUCCESS: 'g++' appears to be installed successfully"
        echo "    "`which g++`
    fi
fi

# Needed for building akima. If we can build a distributable wheel for akima, then maybe
# we won't need this.
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

if [[ "$1" == "settings_repo" ]]; then
    repo_name=$2
    repo_name_string="settings repo $repo_name"
    repo_dir=$GEOIPS_PACKAGES_DIR/$repo_name
    repo_url=$GEOIPS_REPO_URL/${repo_name}.git
    ls $repo_dir/* >> $install_log 2>&1
    retval=$?
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
        if [[ "$clone_retval" == "0" ]]; then
            echo "SUCCESS: Cloned $repo_name_string"
        else
            echo "FAILED: $repo_name_string clone returned non-zero"
            echo "        try deleting directory and re-running"
            exit 1
        fi
    else
        echo "SUCCESS: $repo_name_string appears to be installed successfully"
        echo "    "`ls -ld $repo_dir`
    fi
fi

if [[ "$1" == "test_data" ]]; then
    # Download test data from a known URL into $GEOIPS_TESTDATA_DIR
    test_data_name=$2

    if [[ ! -d $GEOIPS_TESTDATA_DIR ]]; then
        mkdir -p $GEOIPS_TESTDATA_DIR
    fi

    test_data_name_string="tests data repo $test_data_name"
    test_data_dir=$GEOIPS_TESTDATA_DIR/$test_data_name
    for url in ${test_data_urls[@]}; do
        if [[ "${url}" == *"${test_data_name}.tgz" ]]; then
            test_data_url="${url}"
            break
        fi
    done
    data_path="$test_data_dir/data/*"

    ls $data_path >> $install_log 2>&1
    retval=$?

    if [[ "$retval" != "0" ]]; then
        if [[ "$exit_on_missing" == "true" ]]; then
            echo "FAILED: Missing $test_data_name_string"
            echo "        Please run install script, then rerun test script. "
            echo "        $install_script"
            echo "        $test_script"
            exit 1
        fi
        echo "Installing $test_data_name_string .... "
        echo "  $test_data_dir/ from $test_data_url"
        python $SCRIPT_DIR/download_test_data.py $test_data_url | tar -xz -C $GEOIPS_TESTDATA_DIR >> $install_log 2>&1
        dl_retval=$?
        if  [[ "$dl_retval" == "0" ]]; then
            echo "SUCCESS: Pulled and decompressed ${test_data_name} from ${test_data_url}"
        else
            echo "FAILED: Failed to pull and decompress ${test_data_name} from ${test_data_url}"
            echo "        try deleting and re-running"
            exit 1
        fi
    else
        echo "SUCCESS: $test_data_name_string appears to be installed successfully"
        echo "    "`ls -ld $test_data_dir`
    fi
fi

if [[ "$1" == "source_repo" ]]; then
    repo_name=$2

    repo_name_string="source repo $repo_name"
    repo_dir=$GEOIPS_PACKAGES_DIR/$repo_name
    repo_url=$GEOIPS_REPO_URL/${repo_name}.git
    data_path="$repo_dir/tests/*"
    gz_data_path="$repo_dir/tests/outputs/*/*.gz"
    bz2_data_path="$repo_dir/tests/outputs/*/*/*.gz"
    uncompress_script=$GEOIPS_PACKAGES_DIR/$repo_name/tests/uncompress_test_data.sh

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
        echo "pip install -e $repo_dir" >> $install_log 2>&1
        pip install -e $repo_dir >> $install_log 2>&1
        pip_retval=$?
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
