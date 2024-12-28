# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# If this is defined, attempt to switch to this branch after cloning.
# Do not fail if it doesn't exist.
switch_to_branch=$GEOIPS_MODIFIED_BRANCH

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

# Requirements to run base geoips tests
if [[ "$1" == "geoips_base" ]]; then
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh git
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh python
fi

# Requirements to run the full suite of open source geoips tests
if [[ "$1" == "geoips_full" ]]; then
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh geoips_base
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh gcc
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh gfortran
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh g++
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh openblas
fi

if [[ "$1" == "set_gitconfig" ]]; then
    source $GEOIPS_PACKAGES_DIR/geoips/setup/bash_setup/gitconfigs
fi

if [[ "$1" == "run_command" ]]; then
    echo "Running $2 ... "
    `$2 >> $install_log 2>&1`
    if [[ "$?" != "0" ]]; then
        echo "'$2' failed. Quitting"
        exit 1
    else
        echo "SUCCESS: '$2' appears to have run successfully"
    fi
fi

if [[ "$1" == "dump_pip_environment" ]]; then
    output_requirements_txt="$2"
    if [[ ! -d `dirname $output_requirements_txt` ]]; then
        echo "FAILED: `dirname $output_requirements_txt` did not exist"
        echo "        create directory, then re-run"
        exit 1
    fi
    pip freeze > $output_requirements_txt
    if [[ "$?" == "0" ]]; then
        echo "SUCCESS: Dumped pip requirements to $output_requirements_txt"
    else
        echo "FAILED Dumping pip requirements to $output_requirements_txt"
        exit 1
    fi
fi
if [[ "$1" == "dump_mamba_environment" ]]; then
    output_requirements_txt="$2"
    if [[ ! -d `dirname $output_requirements_txt` ]]; then
        echo "FAILED: `dirname $output_requirements_txt` did not exist"
        echo "        create directory, then re-run"
        exit 1
    fi
    mamba list --export > $output_requirements_txt
    if [[ "$?" == "0" ]]; then
        echo "SUCCESS: Dumped mamba package list to $output_requirements_txt"
    else
        echo "FAILED Dumping mamba package list to $output_requirements_txt"
        exit 1
    fi
fi

if [[ "$1" == "check_command" ]]; then
    $2 --version >> $install_log 2>&1
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo "WARNING: '$2 --version' failed, please install $2 before proceeding"
        exit 1
    else
        echo "SUCCESS: '$2' appears to be installed successfully"
        echo "    "`which $2`
    fi
fi

if [[ "$1" == "check_environment_variable" ]]; then
    if [[ -z "${!2}" ]]; then
        echo "WARNING: '\$$2' does not exist, must be defined before proceeding"
        exit 1
    else
        echo "SUCCESS: '\$$2' appears to exist, ${!2}"
    fi
fi

if [[ "$1" == "clone_repo" ]]; then

    if [[ ! -e "$3" ]]; then
	echo "git clone $2 $3"
	git clone $2 $3
	retval=$?
	if [[ "$retval" != "0" ]]; then
            echo "FAILED: '$2' failed cloning, try deleting and try again"
	    echo "$3"
            exit 1
	fi
    elif [[ "$4" != "" ]]; then
	if [[ ! -e "$3/$4" ]]; then
	    echo "FAILED: subdirectory $4 does not exist in $3."
	    echo "Try deleting $3 and trying again"
	    exit 1
	fi
    else
        echo "SUCCESS: '\$$2' appears to already exist, ${!2}"
    fi
fi

if [[ "$1" == "mamba_install" ]]; then
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh check_command $2
    if [[ "$?" != "0" ]]; then
        mamba install $2 -y
    fi
    . $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh check_command $2
    if [[ "$?" != "0" ]]; then
        echo "WARNING: '$2 --version' failed, please install $2 before proceeding"
        exit 1
    else
        echo "SUCCESS: '$2' appears to be installed successfully"
        echo "    "`which $2`
    fi
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
        echo "WARNING: 'python --version' failed, please install python >= 3.9 before proceeding."
	echo "If you have python3 installed, please alias it to python."
        echo "For more info see https://askubuntu.com/a/321000/314655"
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
if [[ "$1" == "gfortran" ]]; then
    gfortran --version >> $install_log 2>&1
    retval=$?
    if [[ "$retval" != "0" ]]; then
        echo "WARNING: 'gfortran --version' failed, please install gfortran before proceeding"
        exit 1
    else
        echo "SUCCESS: 'gfortran' appears to be installed successfully"
        echo "    "`which gfortran`
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
    if [[ "$switch_to_branch" != "" ]]; then
        repo_name_string="$repo_name_string, branch $switch_to_branch"
    fi
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
        # Check if current branch exists, and switch to it if so.
        # Allow branch not existing.
        if [[ "$switch_to_branch" != "" ]]; then
            git -C $repo_dir checkout $switch_to_branch
            if [[ "$?" != "0" ]]; then
                echo "Branch $switch_to_branch did not exist, staying on current branch"
            else
                echo "SUCCESS: successfully switch to branch $switch_to_branch"
            fi
        fi
    else
        echo "SUCCESS: $repo_name_string appears to be installed successfully"
        echo "    "`ls -ld $repo_dir`
    fi
fi

if [[ "$1" == "test_data" || "$1" == "test_data_github" ]]; then
    # Download test data from a known URL into $GEOIPS_TESTDATA_DIR
    test_data_name=$2
    test_data_source_location="cira"
    if [[ "$1" == "test_data_github" ]]; then
        test_data_source_location="github"
    fi

    if [[ ! -d $GEOIPS_TESTDATA_DIR ]]; then
        mkdir -p $GEOIPS_TESTDATA_DIR
    fi

    test_data_name_string="tests data repo $test_data_name"
    if [[ "$switch_to_branch" != "" ]]; then
        test_data_name_string="$test_data_name_string, branch $switch_to_branch"
    fi
    test_data_dir=$GEOIPS_TESTDATA_DIR/$test_data_name
    test_data_url="$GEOIPS_REPO_URL/${test_data_name}.git"
    if [[ "$test_data_source_location" != "github" ]]; then
        test_data_url="direct download"
    fi

    # Ensure there is a data or docs directory
    data_path="$test_data_dir/data/*"
    ls $data_path >> $install_log 2>&1
    retval_data=$?
    data_path="$test_data_dir/docs/*"
    ls $data_path >> $install_log 2>&1
    retval_docs=$?
    data_path="$test_data_dir/outputs/*"
    ls $data_path >> $install_log 2>&1
    retval_outputs=$?
    data_path="$test_data_dir/*.tgz"
    ls $data_path >> $install_log 2>&1
    retval_tgz=$?

    if [[ "$retval_data" != "0" && "$retval_docs" != "0" && "$retval_outputs" != "0" && "$retval_tgz" != "0" ]]; then
        if [[ "$exit_on_missing" == "true" ]]; then
            echo "FAILED: Missing $test_data_name_string"
            echo "        Please run install script, then rerun test script. "
            echo "        $install_script"
            echo "        $test_script"
            exit 1
        fi
        echo "Installing $test_data_name_string .... "
        echo "  $test_data_dir/ using $test_data_url via $test_data_source_location"
        if [[ "$test_data_source_location" == "github" ]]; then
            python3 $SCRIPT_DIR/download_test_data.py $test_data_url --output-dir $GEOIPS_TESTDATA_DIR/${test_data_name} >> $install_log 2>&1
            retval=$?
            if  [[ "$retval" == "0" ]]; then
                echo "SUCCESS: Pulled ${test_data_name} from ${test_data_url}"
            else
                echo "FAILED: Failed to pull ${test_data_name} from ${test_data_url}"
                echo "        try deleting and re-running"
                exit 1
            fi
            # If this is a github repo, then check if current-branch exists
            # and switch to it if so. Allow branch not existing.
            if [[ "$switch_to_branch" != "" ]]; then
                echo "git -C $test_data_dir checkout $switch_to_branch >> $install_log 2>&1"
                git -C $test_data_dir checkout $switch_to_branch >> $install_log 2>&1
                if [[ "$?" != "0" ]]; then
                    echo "Branch $switch_to_branch did not exist, staying on current branch"
                else
                    echo "SUCCESS: successfully switch to branch $switch_to_branch"
                fi
            fi
            if [[ -e $test_data_dir/uncompress_test_data.sh ]]; then
                $test_data_dir/uncompress_test_data.sh >> $install_log 2>&1
                retval=$?
                if  [[ "$retval" == "0" ]]; then
                    echo "SUCCESS: Decompressed ${test_data_name}"
                else
                    echo "FAILED: Failed to decompress ${test_data_name}. Try deleting and rerunning."
                    exit 1
                fi
            fi
        else
            echo "DOWNLOADING: NextCloud Dataset $test_data_name"
            python3 $SCRIPT_DIR/download_test_data.py $test_data_name --output-dir $GEOIPS_TESTDATA_DIR
            # check to see how many folders in GEOIPS_TESTDATA_DIR match test_data_name
            matching_folders=$(ls $GEOIPS_TESTDATA_DIR | grep $test_data_name)
            folder_count=$(echo "$matching_folders" | wc -l)
            if [[ "$folder_count" -ne 1 ]]; then
                echo "Error: Expected exactly one matching folder starting with $test_data_name but found $folder_count."
                echo "Please delete or rename folders starting with $test_data_name in $GEOIPS_TESTDATA_DIR before running this script again."
                exit 1
            fi
            # if only one match was found, this was the installed dataset and we are good
            # to rename the top folder of it to test_data_name. This way full_install.sh will
            # not download the data again as it's able to identify that it's installed.
            folder_name=$(echo "$matching_folders")
            if [[ "$folder_name" != "$test_data_name" ]]; then
                # if folder_name doesn't equal test_data_name then rename that folder
                mv $GEOIPS_TESTDATA_DIR/$folder_name $test_data_dir
            fi
            retval=$?
            if  [[ "$retval" == "0" ]]; then
                echo "SUCCESS: Pulled ${test_data_name} from NexCloud ${test_data_url}"
            else
                echo "FAILED: Failed to pull ${test_data_name} from NexCloud ${test_data_url}"
                echo "        try deleting and re-running"
                exit 1
            fi
        fi
    else
        echo "SUCCESS: $test_data_name_string appears to be installed successfully"
        echo "    "`ls -ld $test_data_dir`
    fi
fi

if [[ "$1" == "source_repo" ]]; then
    repo_name=$2
    if [[ $3 != "exit_on_missing" ]]; then
        pip_arguments=$3
    fi

    repo_name_string="source repo $repo_name"
    if [[ "$switch_to_branch" != "" ]]; then
        repo_name_string="$repo_name_string, branch $switch_to_branch"
    fi
    repo_dir=$GEOIPS_PACKAGES_DIR/$repo_name
    repo_url=$GEOIPS_REPO_URL/${repo_name}.git
    data_path="$repo_dir/tests/*"

    ls $data_path >> $install_log 2>&1
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
        # Check if current branch exists, and switch to it if so.
        # Allow branch not existing.
        if [[ "$switch_to_branch" != "" ]]; then
            git -C $repo_dir checkout $switch_to_branch >> $install_log 2>&1
            if [[ "$?" != "0" ]]; then
                echo "Branch $switch_to_branch did not exist, staying on current branch"
            else
                echo "SUCCESS: successfully switch to branch $switch_to_branch"
            fi
        fi
        pip_retval=0
        echo "pip install -e $repo_dir -v $pip_arguments" >> $install_log 2>&1
        pip install -e $repo_dir -v $pip_arguments >> $install_log 2>&1
        pip_retval=$?
        if [[ "$clone_retval" == "0" && "$pip_retval" == "0" ]]; then
            echo "SUCCESS: Cloned and installed $repo_name_string"
        else
            echo "FAILED: $repo_name_string clone or install returned non-zero"
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
