 | # # # Distribution Statement A. Approved for public release. Distribution unlimited.
 | # # #
 | # # # Author:
 | # # # Naval Research Laboratory, Marine Meteorology Division
 | # # #
 | # # # This program is free software: you can redistribute it and/or modify it under
 | # # # the terms of the NRLMMD License included with this program. This program is
 | # # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
 | # # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
 | # # # for more details. If you did not receive the license, for more information see:
 | # # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

************
Installation
************

Using a fresh Mini/Anaconda Python 3.9 Environment is the easiest way to get geoips up and running.

GeoIPS does not support Python 2 development.

Software Requirements
=====================

Required

* wget (Miniconda and rclone setup)
* git >= 2.19.1 (git -C commands in complete installation)
* git-lfs (required for clones of test data repos)
* imagemagick (required for test output comparisons)
* openblas (required for scipy pip install)

  * included in `Complete Local conda-based GeoIPS Installation`_

* libgeos (required for shapely / cartopy pip install)

  * included in `Complete Local conda-based GeoIPS Installation`_

* Python >= 3.9 (3.9 required for entry points)

  * included in `Complete Local conda-based GeoIPS Installation`_

* rclone (required to obtain ABI and AHI test data from AWS)

  * included in `Complete Local conda-based GeoIPS Installation`_

* Test data repos contained in $GEOIPS_TESTDATA_DIR (required for tests to pass)

  * included in `Complete Local conda-based GeoIPS Installation`_

Optional

* gfortran (only required for plugins including fortran builds)
* gcc (required for plugins including fortran or C builds, build-essential)
* screen (convenience package)
* ncurses (only required if building vim, ncurses and libncurses5-dev)

NOTE: Currently the test outputs are only guaranteed to pass (0 returns from tests)
if cartopy and matplotlib are installed via conda!  Eventually we will update
all test outputs to be generated using a pip-only install of all python packages,
but for now if your tests fail, try installing cartopy and matplotlib via conda
vs pip.

PIP Installation
================

Expert User GeoIPS Installation
-------------------------------

For the fully supported installation, please use the
`Complete Local conda-based GeoIPS Installation`_.

If you are confident you have all system requirements installed (Python+cartopy),
and do not wish to go through the full interactive installation process below
(which includes conda, rclone, test data, etc), you can clone the geoips repo
and pip install from the your local copy.

.. code:: bash

    export GEOIPS_PACKAGES_DIR=<installation_location>
    export GEOIPS_TESTDATA_DIR=<desired_test_data_location>
    export GEOIPS_OUTDIRS=<desired_output_file_location>
    export GEOIPS_REPO_URL=https://github.com/NRLMMD-GEOIPS
    cd <installation location>
    git clone https://github.com/NRLMMD-GEOIPS/geoips/geoips.git <installation_location>
    pip install -e .

Conda Installation
==================

Complete Local conda-based GeoIPS Installation
----------------------------------------------

This is the fully supported installation method, which involves installing the entire
Python environment from scratch using conda, to allow for consistency across
installations.  This process ensures source code, test datasets, etc are all
contained in the same location to facilitate assisting users if issues arise
during the installation, testing, and development process.

This installation method includes the first 4 system requirements (Python, cartopy,
rclone, and test repos) through a complete install of conda, geoips, test repos,
and all Python dependencies.

GeoIPS Environment Variables for Complete conda-based Installation
------------------------------------------------------------------

.. code:: bash

    # Set up appropriate environment variables for conda-based geoips setup steps.
    # The steps within this section will need to be copied and pasted into your shell any time you want to
    # run the conda-based setup commands directly. Typical users do not have to make any modifications to the
    # commands within this README and can copy and paste directly.

    # Once geoips has been installed, the "GEOIPS_CONFIG_FILE" specified below will be sourced when running geoips,
    # and the direct environment variable assignments within this section are no longer required.

    # If you would like to have the GEOIPS_CONFIG_FILE automatically sourced so you do not have to manually run the
    # appropriate source command for every new shell, you can add
    # source </full/path/to/GEOIPS_CONFIG_FILE>
    # to your ~/.bashrc file

    # GeoIPS default required packages
    git lfs install  # Required to clone test data repositories!

    # GeoIPS Default Locations
    export GEOIPS_BASEDIR=$HOME/geoproc  # Contains all source, output, and external dependencies
    export GEOIPS_REPO_URL=https://github.com/NRLMMD-GeoIPS  # Point to base URL for git clone commands
    GEOIPS_ACTIVE_BRANCH=main
    export GEOIPS_PACKAGES_DIR=$GEOIPS_BASEDIR/geoips_packages
    export GEOIPS_TESTDATA_DIR=$GEOIPS_BASEDIR/test_data
    export GEOIPS_DEPENDENCIES_DIR=$GEOIPS_BASEDIR/geoips_dependencies

    # GeoIPS default configuration - must be source ANY TIME you want to run GeoIPS
    # You can create your own user/site specific version to replace this one as needed.
    export GEOIPS_CONFIG_FILE=$GEOIPS_PACKAGES_DIR/geoips/setup/config_geoips


Complete conda-based Installation and Test
------------------------------------------

.. code:: bash

    # Initial clone of geoips repo, to obtain setup scripts
    mkdir -p $GEOIPS_PACKAGES_DIR
    git clone $GEOIPS_REPO_URL/geoips.git $GEOIPS_PACKAGES_DIR/geoips

    # This just makes sure you are *really* on $GEOIPS_ACTIVE_BRANCH
    git -C $GEOIPS_PACKAGES_DIR/geoips pull
    git -C $GEOIPS_PACKAGES_DIR/geoips checkout -t origin/$GEOIPS_ACTIVE_BRANCH
    git -C $GEOIPS_PACKAGES_DIR/geoips checkout $GEOIPS_ACTIVE_BRANCH
    git -C $GEOIPS_PACKAGES_DIR/geoips pull

    # These helper scripts will just confirm all required system requirements are available.
    # Please confirm output before proceeding with base_install_and_test.sh
    $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh wget
    $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh gitlfs
    $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh imagemagick
    $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh git

    # This prompts you through all the steps of installing geoips from scratch, using the parameters specified above
    # Installs and tests everything!
    # Requires <30GB disk space, <8GB memory
    # Low memory option. No high res Visible outputs.  Same setup, just different tests.
    $GEOIPS_PACKAGES_DIR/geoips/base_install_and_test.sh $GEOIPS_ACTIVE_BRANCH low_memory low_bandwidth conda-forge

    # Requires <30GB disk space, <16GB memory
    # This includes all channels for the ABI test case, and Visible test outputs
    # higher bandwidth and higher memory requirements than the low_memory low_bandwidth version above
    # $GEOIPS_PACKAGES_DIR/geoips/base_install_and_test.sh $GEOIPS_ACTIVE_BRANCH
