#### # # Distribution Statement A. Approved for public release. Distribution unlimited.
#### # # 
#### # # Author:
#### # # Naval Research Laboratory, Marine Meteorology Division
#### # # 
#### # # This program is free software:
#### # # you can redistribute it and/or modify it under the terms
#### # # of the NRLMMD License included with this program.
#### # # 
#### # # If you did not receive the license, see
#### # # https://github.com/U-S-NRL-Marine-Meteorology-Division/
#### # # for more information.
#### # # 
#### # # This program is distributed WITHOUT ANY WARRANTY;
#### # # without even the implied warranty of MERCHANTABILITY
#### # # or FITNESS FOR A PARTICULAR PURPOSE.
#### # # See the included license for more details.

Installation Guide
==================

Using a fresh Mini/Anaconda Python 3.8 or 3.9 Environment is the easiest way to get geoips up and running.

geoips does not support Python 2 development.


Setup System Environment Variables
----------------------------------

```bash

    # Set up appropriate environment variables for conda-based geoips setup steps within this README below.
    # The steps within this section will need to be copied and pasted into your shell any time you want to
    # run the setup commands within this README. Typical users do not have to make any modifications to the
    # commands within this README and can copy and paste directly.

    # Once geoips has been installed, the "GEOIPS_CONFIG_FILE" specified below will be sourced when running geoips,
    # and the direct environment variable assignments within this section are no longer required.

    # If you would like to have the GEOIPS_CONFIG_FILE automatically sourced so you do not have to manually run the 
    # appropriate source command for every new shell, you can add 
    # source </full/path/to/GEOIPS_CONFIG_FILE>
    # to your ~/.bashrc file

    # If you have sudo/apt access to your system, ensure all required libraries are available
    # sudo apt-get update               # Make sure apt packages are up to date
    # sudo apt install wget             # Required for Miniconda and rclone setup
    # sudo apt install git              # Required for all git clones, >=2.19.1
    # sudo apt install imagemagick      # Required for test output comparisons
    # sudo apt install gfortran         # OPTIONAL - Required if you have plugins with fortran builds
    # sudo apt install build-essential  # OPTIONAL - Required if you have plugins with fortran/C builds
    # sudo apt install screen           # OPTIONAL - convenience package
    # sudo apt install ncurses          # OPTIONAL - Required for vim build
    # sudo apt install libncurses5-dev  # OPTIONAL - Required for vim build

    # GEOIPS_BASEDIR will contain all source, output, and external dependencies
    # Ensure this is consistently set for all installation / setup steps below
    export GEOIPS_BASEDIR=$HOME/geoproc

    # GEOIPS_REPO_URL should point to the base URL for git clone commands
    export GEOIPS_REPO_URL=https://github.com/NRLMMD-GeoIPS

    # This config file must be sourced ANY TIME you want to run geoips
    export GEOIPS_CONFIG_FILE=$GEOIPS_BASEDIR/geoips_packages/geoips/setup/config_geoips

    GEOIPS_ACTIVE_BRANCH=dev
```


Base geoips installation and test
----------------------------------
```
    # Initial clone of geoips repo, to obtain setup scripts
    mkdir -p $GEOIPS_BASEDIR/geoips_packages
    git clone $GEOIPS_REPO_URL/geoips.git $GEOIPS_BASEDIR/geoips_packages/geoips
    
    git -C $GEOIPS_BASEDIR/geoips_packages/geoips pull
    git -C $GEOIPS_BASEDIR/geoips_packages/geoips checkout -t origin/$GEOIPS_ACTIVE_BRANCH
    git -C $GEOIPS_BASEDIR/geoips_packages/geoips checkout $GEOIPS_ACTIVE_BRANCH
    git -C $GEOIPS_BASEDIR/geoips_packages/geoips pull

    # This prompts you through all the steps of installing geoips from scratch, using the parameters specified above
    # Installs and tests everything!
    $GEOIPS_BASEDIR/geoips_packages/geoips/base_install_and_test.sh $GEOIPS_ACTIVE_BRANCH
```
