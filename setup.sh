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

if [[ -z "$GEOIPS_BASEDIR" ]]; then
    echo "Must define GEOIPS_BASEDIR environment variable prior to setting up geoips"
    exit 1
fi

# This sets required environment variables for setup - without requiring sourcing a geoips config in advance
. $GEOIPS_BASEDIR/geoips_packages/geoips/setup/repo_clone_update_install.sh setup

umask 0002

if [[ ! -d $GEOIPS_DEPENDENCIES_DIR/bin ]]; then
    mkdir $GEOIPS_DEPENDENCIES_DIR/bin
fi
if [[ "$1" == "conda_install" ]]; then
    echo ""
    # echo "**wgetting Anaconda3*.sh"
    # wget https://repo.anaconda.com/archive/Anaconda3-2021.05-Linux-x86_64.sh -P $GEOIPS_DEPENDENCIES_DIR
    # chmod 755 $GEOIPS_DEPENDENCIES_DIR/Anaconda3-*.sh
    echo "**wgetting Miniconda3*.sh"
    opsys=Linux
    arch=$(uname -m)
    if [[ "$(uname -s)" == "Darwin" ]]; then
        opsys=MacOSX
    fi
    conda_fname=Miniconda3-latest-${opsys}-${arch}.sh
    wget https://repo.anaconda.com/miniconda/${conda_fname} -P $GEOIPS_DEPENDENCIES_DIR
    chmod 755 $GEOIPS_DEPENDENCIES_DIR/${conda_fname}
    echo ""
    echo "**Running Anaconda3*.sh"
    # $GEOIPS_DEPENDENCIES_DIR/Anaconda3-*.sh -p $GEOIPS_DEPENDENCIES_DIR/anaconda3
    $GEOIPS_DEPENDENCIES_DIR/${conda_fname} -p $GEOIPS_DEPENDENCIES_DIR/miniconda3
    echo ""
    # echo "**If shell initialized, MUST source ~/.bashrc or restart shell"
    # source ~/.bashrc
    # echo "source ~/.bashrc"
    source $GEOIPS_PACKAGES_DIR/geoips/setup/geoips_conda_init_setup
elif [[ "$1" == "conda_link" ]]; then
    echo ""
    echo "**Linking conda to bin"
    mkdir -p $GEOIPS_DEPENDENCIES_DIR/bin
    ln -sfv $BASECONDAPATH/conda $GEOIPS_DEPENDENCIES_DIR/bin
elif [[ "$1" == "conda_init" ]]; then
    echo ""
    echo "**Initializing conda"
    conda init
    # Link conda to geoips_dependencies/bin so it is in path
    $GEOIPS_BASEDIR/geoips_packages/geoips/setup.sh conda_link
    echo ""
    # echo "**IF SCRIPT WAS NOT SOURCED MUST source ~/.bashrc or restart shell"
    # source ~/.bashrc
    # echo "source ~/.bashrc"
    source $GEOIPS_PACKAGES_DIR/geoips/setup/geoips_conda_init_setup
elif [[ "$1" == "conda_update" ]]; then
    echo ""
    echo "**updating base conda env"
    which conda
    which python
    conda update -n base -c defaults conda --yes
elif [[ "$1" == "remove_geoips_conda_env" ]]; then
    echo ""
    echo "**removing geoips_conda env"
    which conda
    which python
    echo "**IF SCRIPT WAS NOT SOURCED MUST first deactivate geoips_conda env from parent shell"
    conda deactivate
    echo "conda deactivate"
    conda env remove --name geoips_conda
elif [[ "$1" == "create_geoips_conda_env" ]]; then
    echo ""
    echo "**creating geoips_conda env"
    which conda
    which python
    conda create --yes --name geoips_conda python=3.9 --yes
    echo "**IF SCRIPT WAS NOT SOURCED MUST activate geoips_conda env from parent shell"
    conda activate geoips_conda
    echo "conda activate geoips_conda"
elif [[ "$1" == "install" ]]; then
    echo ""
    echo "**Installing cartopy"
    # cartopy 0.19.0 and matplotlib 3.4.0 both cause slightly shifted figures compared to old versions
    # Updating test outputs to latest versions
    # $BASECONDAPATH/conda install -c conda-forge cartopy matplotlib
    # This was getting 0.18.0 sometimes without specifying version ???  Force to 0.20.0

    # Update to latest 20220607, previously cartopy 0.20.2 and matplotlib 3.4.3.
    conda install -c conda-forge "cartopy>=0.20.2" "matplotlib>=3.5.2" --yes

    pip install -e "$GEOIPS_PACKAGES_DIR/geoips[efficiency_improvements,\
                                                  test_outputs,\
                                                  config_based,\
                                                  hdf5_readers,\
                                                  hdf4_readers,\
                                                  geotiff_output,\
                                                  syntax_checking,\
                                                  documentation,\
                                                  debug,\
                                                  overpass_predictor,\
                                                  coverage_checks,\
                                                  geostationary_readers]"

elif [[ "$1" == "setup_abi_test_data" ]]; then
    # rclone lsf publicAWS:noaa-goes16/ABI-L1b-RadF/2020/184/16/
    abidir=$GEOIPS_TESTDATA_DIR/goes16_20200918_1950
    mkdir -p $abidir
    echo "** Setting up abi test data, from publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19/ to $abidir"
    echo ""
    echo "NOAA Geostationary Operational Environmental Satellites (GOES) 16 & 17 was accessed on "
    echo `date -u` "from https://registry.opendata.aws/noaa-goes."
    echo ""

    rclone copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19/OR_ABI-L1b-RadF-M6C01_G16_s20202621950205_e20202621959513_c20202621959567.nc $abidir
    rclone copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19/OR_ABI-L1b-RadF-M6C02_G16_s20202621950205_e20202621959513_c20202621959546.nc $abidir
    rclone copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19/OR_ABI-L1b-RadF-M6C03_G16_s20202621950205_e20202621959513_c20202621959570.nc $abidir
    rclone copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19/OR_ABI-L1b-RadF-M6C04_G16_s20202621950205_e20202621959513_c20202621959534.nc $abidir
    rclone copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19/OR_ABI-L1b-RadF-M6C05_G16_s20202621950205_e20202621959513_c20202621959562.nc $abidir
    rclone copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19/OR_ABI-L1b-RadF-M6C06_G16_s20202621950205_e20202621959518_c20202621959556.nc $abidir
    rclone copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19/OR_ABI-L1b-RadF-M6C07_G16_s20202621950205_e20202621959524_c20202621959577.nc $abidir
    rclone copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19/OR_ABI-L1b-RadF-M6C08_G16_s20202621950205_e20202621959513_c20202621959574.nc $abidir
    rclone copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19/OR_ABI-L1b-RadF-M6C09_G16_s20202621950205_e20202621959518_c20202621959588.nc $abidir
    rclone copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19/OR_ABI-L1b-RadF-M6C10_G16_s20202621950205_e20202621959524_c20202621959578.nc $abidir
    rclone copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19/OR_ABI-L1b-RadF-M6C11_G16_s20202621950205_e20202621959513_c20202621959583.nc $abidir
    rclone copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19/OR_ABI-L1b-RadF-M6C12_G16_s20202621950205_e20202621959518_c20202621959574.nc $abidir
    rclone copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19/OR_ABI-L1b-RadF-M6C13_G16_s20202621950205_e20202621959525_c20202622000005.nc $abidir
    rclone copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19/OR_ABI-L1b-RadF-M6C14_G16_s20202621950205_e20202621959513_c20202622000009.nc $abidir
    rclone copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19/OR_ABI-L1b-RadF-M6C15_G16_s20202621950205_e20202621959518_c20202621959594.nc $abidir
    rclone copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19/OR_ABI-L1b-RadF-M6C16_G16_s20202621950205_e20202621959524_c20202622000001.nc $abidir

elif [[ "$1" == "setup_seviri" ]]; then
    mkdir -p $GEOIPS_DEPENDENCIES_DIR/seviri_wavelet
    cwd=`pwd`
    cd $GEOIPS_DEPENDENCIES_DIR/seviri_wavelet
    git clone https://gitlab.eumetsat.int/open-source/PublicDecompWT.git
    cd $cwd
    make all -C $GEOIPS_DEPENDENCIES_DIR/seviri_wavelet/PublicDecompWT/xRITDecompress
    mkdir -p $GEOIPS_DEPENDENCIES_DIR/bin
    ln -sfv $GEOIPS_DEPENDENCIES_DIR/seviri_wavelet/PublicDecompWT/xRITDecompress/xRITDecompress $GEOIPS_DEPENDENCIES_DIR/bin/xRITDecompress
elif [[ "$1" == "setup_rclone" ]]; then
    mkdir -p $GEOIPS_DEPENDENCIES_DIR/rclone
    opsys=linux
    arch=$(uname -m)
    if [[ "$(uname -s)" == "Darwin" ]]; then
        opsys=osx
    fi
    # Annoying
    if [[ "$(uname -m)" == "x86_64" ]]; then
        arch=amd64
    fi
    wget https://downloads.rclone.org/rclone-current-${opsys}-${arch}.zip -P $GEOIPS_DEPENDENCIES_DIR/rclone
    cd $GEOIPS_DEPENDENCIES_DIR/rclone
    # This puts it in the current directory
    unzip $GEOIPS_DEPENDENCIES_DIR/rclone/rclone-current-${opsys}-${arch}.zip
    # rclone-current expands into rclone-<vers>, not rclone-current, so link arbitrary rclone* subdirectory
    ln -sfv ${GEOIPS_DEPENDENCIES_DIR}/rclone*/rclone*/rclone ${GEOIPS_DEPENDENCIES_DIR}/bin/rclone
    mkdir -p ~/.config/rclone/
    ln -sv ${GEOIPS_PACKAGES_DIR}/geoips/setup/rclone_setup/rclone.conf ~/.config/rclone 
    if [[ $? != 0 ]]; then
        echo ""
        echo "**********"
        echo "WARNING: rclone.conf not initiated in ~/.config"
        echo "    If you want to replace ~/.config/rclone/rclone.conf with geoips version, run the following:"
        echo "    ln -sfv ${GEOIPS_PACKAGES_DIR}/geoips/setup/rclone_setup/rclone.conf ~/.config/rclone"
        echo "**********"
    fi
elif [[ "$1" == "setup_vim8" ]]; then
    mkdir -p $GEOIPS_DEPENDENCIES_DIR/vim8_build
    cwd=`pwd`
    cd $GEOIPS_DEPENDENCIES_DIR/vim8_build
    git clone https://github.com/vim/vim.git
    cd vim
    ./configure --prefix=${GEOIPS_DEPENDENCIES_DIR}/vim8_build/vim --disable-nls --enable-cscope --enable-gui=no --enable-multibyte --enable-pythoninterp --with-features=huge --with-tlib=ncurses --without-x;
    make
    make install
    mkdir -p $GEOIPS_DEPENDENCIES_DIR/bin
    ln -s $GEOIPS_DEPENDENCIES_DIR/vim8_build/vim/bin/vim $GEOIPS_DEPENDENCIES_DIR/bin/vi
    ln -s $GEOIPS_DEPENDENCIES_DIR/vim8_build/vim/bin/vim $GEOIPS_DEPENDENCIES_DIR/bin/vim
    cd $cwd
elif [[ "$1" == "setup_vim8_plugins" ]]; then
    mkdir -p $GEOIPS_DEPENDENCIES_DIR/vimdotdir/pack/plugins/start
    cwd=`pwd`
    cd $GEOIPS_DEPENDENCIES_DIR/vimdotdir/pack/plugins/start
    git clone https://github.com/w0rp/ale.git
    cd $cwd
    pip install flake8
    pip install pylint
    pip install bandit
    mkdir -p ~/.vim/pack
    ## If ~/.vim/pack does not exist, link it, otherwise link the contents appropriately.
    echo ""
    ln -sv $GEOIPS_DEPENDENCIES_DIR/vimdotdir/pack/* ~/.vim/pack
    if [[ $? != 0 ]]; then
        echo "If you want to replace ~/.vim/pack with geoips version, run the following:"
        echo "ln -sfv $GEOIPS_DEPENDENCIES_DIR/vimdotdir/pack/* ~/.vim/pack"
    fi
    echo ""
    ## Either add the contents of vimrc_ale to your ~/.vimrc, or replace it
    ln -sv $GEOIPS_PACKAGES_DIR/geoips/setup/bash_setup/vimrc_ale ~/.vimrc
    if [[ $? != 0 ]]; then
        echo "If you want to replace ~/.vimrc with geoips ALE version, run the following:"
        echo "ln -sfv $GEOIPS_PACKAGES_DIR/geoips/setup/bash_setup/vimrc_ale ~/.vimrc"
    fi
elif [[ "$1" == "download_cartopy_natural_earth" ]]; then
    echo ""
    echo "**Installing github.com/nvkelso/natural-earth-vector map data v5.2.0, this will take a while"
    cartopy_data=$GEOIPS_DEPENDENCIES_DIR/cartopy_map_data
    echo "    destination: $cartopy_data"
    mkdir -p $cartopy_data
    cwd=`pwd`
    cd $cartopy_data
    git clone https://github.com/nvkelso/natural-earth-vector
    cd natural-earth-vector
    git fetch --all --tags --prune
    # Previously 5.0.0, 20220607 5.2.0
    # echo "    **Checking out tag v5.2.0, to ensure tests pass"
    # git checkout tags/v5.2.0
    cd $cwd
elif [[ "$1" == "link_cartopy_natural_earth" ]]; then
    echo ""
    echo "**Linking natural-earth-data to ~/.local/share/cartopy/shapefiles/natural_earth/cultural and physical"
    cartopy_data=$GEOIPS_DEPENDENCIES_DIR/cartopy_map_data
    local_natural_earth_path=~/.local/share/cartopy/shapefiles/natural_earth
    mkdir -p $local_natural_earth_path/cultural
    mkdir -p $local_natural_earth_path/physical
    ln -sfv $cartopy_data/natural-earth-vector/*_cultural/*/* $local_natural_earth_path/cultural
    ln1_retval=$?
    ln -sfv $cartopy_data/natural-earth-vector/*_physical/*/* $local_natural_earth_path/physical
    ln2_retval=$?
    ln -sfv $cartopy_data/natural-earth-vector/*_cultural/* $local_natural_earth_path/cultural
    ln3_retval=$?
    ln -sfv $cartopy_data/natural-earth-vector/*_physical/* $local_natural_earth_path/physical
    ln4_retval=$?
    if [[ $ln1_retval != 0 || $ln2_retval != 0 || $ln3_retval != 0 || $ln4_retval != 0 ]]; then
        echo "**You MUST be able to replace ALL user cartopy data with natural_earth_vector downloads!"
        echo "Please remove cartopy shapefiles and replace with downloaded cartopy_map_data"
        echo "rm -fv ~/.local/share/cartopy/shapefiles/natural_earth/cultural/*"
        echo "rm -fv ~/.local/share/cartopy/shapefiles/natural_earth/physical/*"
        echo "ln -sfv $cartopy_data/natural-earth-vector/*_cultural/* $local_natural_earth_path/cultural"
        echo "ln -sfv $cartopy_data/natural-earth-vector/*_physical/* $local_natural_earth_path/physical"
        exit 1
    fi
elif [[ "$1" =~ "clone_test_repo" ]]; then
    echo ""
    echo "**Cloning $2.git"

    repo_name=$2
    repo_url=$GEOIPS_REPO_URL/$repo_name

    # If reponame of format "GEOIPS/geoips" then pull out org and reponame separately
    # "/geoips" would indicate top level (no sub-org)
    if [[ `echo "$2" | grep '/'` != "" ]]; then
        repo_org=`echo "$2" | cut -f 1 -d '/'`
        repo_name=`echo "$2" | cut -f 2 -d '/'`
        if [[ "$GEOIPS_BASE_URL" != "" ]]; then
            repo_url=$GEOIPS_BASE_URL/$repo_org/$repo_name
        else
            repo_url=`dirname $GEOIPS_REPO_URL`/$repo_org/$repo_name
        fi
    fi 

    git clone $repo_url.git $GEOIPS_TESTDATA_DIR/$repo_name
    retval=$?
    echo "git clone return: $retval"
    if [[ $retval != 0 ]]; then
        echo "**You can ignore 'fatal: destination path already exists' - just means you already have the repo"
    fi
elif [[ "$1" =~ "update_test_repo" ]]; then
    if [[ "$3" == "" ]]; then
        branch=main
    else
        branch=$3
    fi
    if [[ "$4" == "do_not_fail" ]]; then
        do_not_fail="do_not_fail"
    else
        do_not_fail=""
    fi
    currdir=$GEOIPS_TESTDATA_DIR/$2
    echo ""
    echo "**Updating test repo $2 branch $branch"
    cwd=`pwd`
    cd $GEOIPS_TESTDATA_DIR/$2
    git pull
    git checkout -t origin/$branch
    retval_t=$?
    git checkout $branch
    retval=$?
    git pull
    git pull
    retval_pull=$?
    cd $cwd
    echo "git checkout -t return: $retval_t"
    echo "git checkout return: $retval"
    echo "git pull return: $retval_pull"
    if [[ $retval != 0 || $retval_t != 0 ]]; then
        echo "**You can ignore 'fatal: A branch named <branch> already exists' - just means you already have the branch"
    fi
    if [[ $retval != 0 && $retval_t != 0 && "$do_not_fail" != "do_not_fail" ]]; then
        echo "*****GIT CHECKOUT FAILED ON $currdir $branch PLEASE APPROPRIATELY commit (if you want to save your changes), checkout (if you do not want to save changes of a git-tracked file), or delete (if you do not want to save changes of an untracked file) ANY LOCALLY MODIFIED FILES AND RERUN repo_update COMMAND. This will ensure you have the latest version of all repos!!!!!!!!"
        exit 1
    fi
    if [[ $retval_pull != 0 && "$do_not_fail" != "do_not_fail" ]]; then
        echo "*****GIT PULL FAILED ON $currdir $branch PLEASE APPROPRIATELY commit (if you want to save your changes), checkout (if you do not want to save changes of a git-tracked file), or delete (if you do not want to save changes of an untracked file) ANY LOCALLY MODIFIED FILES AND RERUN repo_update COMMAND. This will ensure you have the latest version of all repos!!!!!!!!"
        exit 1
    fi
elif [[ "$1" == "uncompress_test_data" ]]; then
    echo ""
    echo "Attempting uncompress $2..."
    testdata_path=$GEOIPS_TESTDATA_DIR/$2/uncompress_test_data.sh
    packages_path=$GEOIPS_PACKAGES_DIR/$2/tests/uncompress_test_data.sh

    uncompress_script=""
    if [[ -e $testdata_path ]]; then
        uncompress_script=$testdata_path
    elif [[ -e $packages_path ]]; then
        uncompress_script=$packages_path
    fi

    if [[ $uncompress_script != "" ]]; then
        echo "     $uncompress_script..."
        $uncompress_script
        retval=$?
        if [[ $retval != 0 ]]; then
            echo "******FAILED uncompress_test_data - please resolve and rerun uncompress_test_data command"
            exit 1
        fi
    fi

elif [[ "$1" == "recompress_test_data" ]]; then
    echo ""
    echo "Attempting recompress $2..."

    testdata_path=$GEOIPS_TESTDATA_DIR/$2/recompress_test_data.sh
    packages_path=$GEOIPS_PACKAGES_DIR/$2/tests/recompress_test_data.sh

    recompress_script=""
    if [[ -e $testdata_path ]]; then
        recompress_script=$testdata_path
    elif [[ -e $packages_path ]]; then
        recompress_script=$packages_path
    fi
    if [[ -e $recompress_script ]]; then
        echo "     $recompress_script..."
        $recompress_script
        retval=$?
        if [[ $retval != 0 ]]; then
            echo "******FAILED uncompress_test_data - please resolve and rerun uncompress_test_data command"
            exit 1
        fi
    fi
elif [[ "$1" =~ "clone_source_repo" ]]; then
    echo ""
    echo "**Cloning $2.git"

    repo_name=$2
    repo_url=$GEOIPS_REPO_URL/$repo_name

    # If reponame of format "GEOIPS/geoips" then pull out org and reponame separately
    # "/geoips" would indicate top level (no sub-org)
    if [[ `echo "$2" | grep '/'` != "" ]]; then
        repo_org=`echo "$2" | cut -f 1 -d '/'`
        repo_name=`echo "$2" | cut -f 2 -d '/'`
        if [[ "$GEOIPS_BASE_URL" != "" ]]; then
            repo_url=$GEOIPS_BASE_URL/$repo_org/$repo_name
        else
            repo_url=`dirname $GEOIPS_REPO_URL`/$repo_org/$repo_name
        fi
    fi 

    git clone $repo_url.git $GEOIPS_PACKAGES_DIR/$repo_name
    retval=$?
    echo "git clone return: $retval"
    if [[ $retval != 0 ]]; then
        echo "**You can ignore 'fatal: destination path already exists' - just means you already have the repo"
    fi
elif [[ "$1" =~ "update_source_repo" ]]; then
    if [[ "$3" == "" ]]; then
        branch=main
    else
        branch=$3
    fi
    if [[ "$4" == "do_not_fail" ]]; then
        do_not_fail="do_not_fail"
    else
        do_not_fail=""
    fi
    currdir=$GEOIPS_PACKAGES_DIR/$2
    echo ""
    echo "**Updating $2 branch $branch"
    cwd=`pwd`
    cd $GEOIPS_PACKAGES_DIR/$2
    git pull
    git checkout -t origin/$branch
    retval_t=$?
    git checkout $branch
    retval=$?
    git pull
    git pull
    cd $cwd
    retval_pull=$?
    echo "git checkout -t return: $retval_t"
    echo "git checkout return: $retval"
    echo "git pull return: $retval_pull"
    if [[ $retval != 0 || $retval_t != 0 ]]; then
        echo "**You can ignore 'fatal: A branch named <branch> already exists' - just means you already have the branch"
    fi
    if [[ $retval != 0 && $retval_t != 0 && "$do_not_fail" != "do_not_fail" ]]; then
        echo "*****GIT CHECKOUT FAILED ON $currdir $branch PLEASE APPROPRIATELY commit (if you want to save your changes), checkout (if you do not want to save changes of a git-tracked file), or delete (if you do not want to save changes of an untracked file) ANY LOCALLY MODIFIED FILES AND RERUN repo_update COMMAND. This will ensure you have the latest version of all repos!!!!!!!!"
        exit 1
    fi
    if [[ $retval_pull != 0 && "$do_not_fail" != "do_not_fail" ]]; then
        echo "*****GIT PULL FAILED ON $currdir $branch PLEASE APPROPRIATELY commit (if you want to save your changes), checkout (if you do not want to save changes of a git-tracked file), or delete (if you do not want to save changes of an untracked file) ANY LOCALLY MODIFIED FILES AND RERUN repo_update COMMAND. This will ensure you have the latest version of all repos!!!!!!!!"
        exit 1
    fi
elif [[ "$1" =~ "clone_external_repo" ]]; then
    echo ""
    echo "**Cloning external repo $2"
    if [[ "$2" == "archer" ]]; then
        git clone https://github.com/ajwimmers/archer $GEOIPS_PACKAGES_DIR/archer
        retval=$?
        echo "git clone return: $retval"
    else
        echo "Unknown external repo"
    fi
    if [[ $retval != 0 ]]; then
        echo "**You can ignore 'fatal: destination path already exists' - just means you already have the repo"
    fi
elif [[ "$1" =~ "run_git_cmd" ]]; then
    gitbasedir=$GEOIPS_PACKAGES_DIR
    if [[ "$4" != "" ]]; then
        gitbasedir=$4
    fi
    echo ""
    echo "**Running cd $gitbasedir/$2; git $3"
    cwd=`pwd`
    cd $gitbasedir/$2
    git $3
    cd $cwd
    retval=$?
    echo "git $3 return: $retval"
elif [[ "$1" =~ "update_external_repo" ]]; then
    currdir=$GEOIPS_PACKAGES_DIR/$2
    if [[ "$3" == "do_not_fail" ]]; then
        do_not_fail="do_not_fail"
    else
        do_not_fail=""
    fi
    echo ""
    echo "**Updating external repo $2"
    cwd=`pwd`
    cd $GEOIPS_PACKAGES_DIR/$2
    git pull
    cd $cwd
    retval=$?
    echo "git pull return: $retval"
    if [[ $retval != 0 && "$do_not_fail" != "do_not_fail" ]]; then
        echo "*****GIT PULL FAILED ON $currdir PLEASE APPROPRIATELY commit (if you want to save your changes), checkout (if you do not want to save changes of a git-controlled file), or delete (if you do not want to save changes of a non-git-controlled file) ANY LOCALLY MODIFIED FILES AND RERUN repo_update COMMAND. This will ensure you have the latest version of all repos!!!!!!!!"
        exit 1
    fi
elif [[ "$1" =~ "install_plugin" ]]; then
    plugin=$2
    installed_plugins_path=$GEOIPS_BASEDIR/installed_geoips_plugins.txt
    echo ""
    echo "**Installing plugin $plugin"
    # First check if setup_<package>.sh exists
    if [[ -f $GEOIPS_PACKAGES_DIR/$2/setup_$2.sh ]]; then
        echo "**Found setup_$2.sh: Running $2/setup_$2.sh install_$2"
        $GEOIPS_PACKAGES_DIR/$2/setup_$2.sh install_$2
        retval=$?
    # Next check if setup.sh exists
    elif [[ -f $GEOIPS_PACKAGES_DIR/$2/setup.sh ]]; then
        echo "**Found setup.sh: Running $2/setup.sh install"
        $GEOIPS_PACKAGES_DIR/$2/setup.sh install
        retval=$?
    # Next check if setup.py exists
    elif [[ -f $GEOIPS_PACKAGES_DIR/$2/setup.py ]]; then
        echo "**Found setup.py: pip installing plugin $2"
        pip install -e $GEOIPS_PACKAGES_DIR/$2
        retval=$?
    fi
    if [[ $retval != 0 ]]; then
        echo "**Failed installing plugin $2, skipping! Must include one of the following setup options:"
        echo "**1. setup_$2.sh install_$2"
        echo "**2. setup.sh install"
        echo "**3. setup.py -> Installed via 'pip install -e $GEOIPS_PACKAGES_DIR/$2'"
    elif [[ -f $installed_plugins_path ]]; then
        echo ""
        echo "Adding plugin $plugin to list $installed_plugins_path, will not reinstall"
        echo "$plugin" >> $installed_plugins_path
    fi
    echo ""
else
    echo "UNRECOGNIZED COMMAND $1"
    exit 1
fi
exit 0
