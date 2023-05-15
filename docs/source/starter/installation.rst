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

Using a fresh Mini/Anaconda Python 3.9+ Environment is the easiest way to
get geoips up and running.

Below we detail two installation methods for geoips:

* A minimal `Expert User GeoIPS Installation`_
  (may require administrative privileges)
* A `Complete Local conda-based GeoIPS Installation`_ (recommended)

System Dependencies
===================

Required (included in `Complete Local conda-based GeoIPS Installation`_)

* wget (Miniconda and rclone setup)
* git >= 2.19.1 (git -C commands in complete installation)
* git-lfs (required for clones of test data repos)
* imagemagick (required for test output comparisons)
* openblas (required for scipy pip install)
* libgeos (required for shapely / cartopy pip install)
* Python >= 3.9 (3.9 required for entry points)
* rclone (required to obtain ABI and AHI test data from AWS)
* Test data repos contained in $GEOIPS_TESTDATA_DIR
  (required for tests to pass)

Optional

* gfortran (only required for plugins including fortran builds,
  build-essential)
* gcc (required for plugins including fortran or C builds, build-essential)
* screen (convenience package)
* ncurses (only required if building vim, ncurses and libncurses5-dev)

Expert User GeoIPS Installation
===============================

For the fully supported installation, please use the
`Complete Local conda-based GeoIPS Installation`_.

If you are confident you have all system requirements installed
(Python+cartopy), and do not wish to go through the full
installation process (which includes conda, rclone, test data, etc),
you can clone the geoips repo and pip install from your local copy.

.. code:: bash

    export GEOIPS_REPO_URL=https://github.com/NRLMMD-GEOIPS
    export GEOIPS_PACKAGES_DIR=<installation_location>
    export GEOIPS_TESTDATA_DIR=<desired_test_data_location>
    export GEOIPS_OUTDIRS=<desired_output_file_location>

    git clone https://github.com/NRLMMD-GEOIPS/geoips/geoips.git $GEOIPS_PACKAGES_DIR/geoips
    pip install -e $GEOIPS_PACKAGES_DIR/geoips
    $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/base_install.sh
    $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/base_test.sh


Complete Local conda-based GeoIPS Installation
==============================================

The following instructions will guide you through installing GeoIPS using
Anaconda Python. This installation method allows users to install GeoIPS without
requiring administrative privileges by using Conda to install all of the
"Required" system dependencies listed above, then installing geoips into
that conda environment.

1. Install Anaconda or Miniconda
--------------------------------

- Download the appropriate version of `Conda
  <https://www.anaconda.com/download#downloads>`_,  `Miniconda
  <https://docs.conda.io/en/latest/miniconda.html>`_, or
  `Miniforge/Mambaforge <https://github.com/conda-forge/miniforge#download>`_.

  For example, for Linux with Intel chips, one of the following:

  .. code:: bash

      # wget https://repo.anaconda.com/archive/Anaconda3-2023.03-1-Linux-x86_64.sh
      # wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
      # wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
      wget https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh

- Make the install script executable and run the installer,
  following the prompts (particularly the bit about
  conda init / restarting terminal!):

  .. code:: bash

      chmod u+x Mambaforge-Linux-x86_64.sh
      ./Mambaforge-Linux-x86_64.sh
      # Follow instructions regarding conda init / restarting your terminal !

2. Set GeoIPS Environment Variables
-----------------------------------

In order to support GeoIPS' testing infrastructure, there are a few required
environment variables. The following should be added to your ``$HOME/.bashrc``
file. You can change your installation location by changing the value of
``$GEOIPS_PACKAGES_DIR``.

If you would like to install GeoIPS in `$HOME/geoips`:

.. code:: bash

    # GeoIPS Default Locations
    export GEOIPS_REPO_URL=https://github.com/NRLMMD-GeoIPS  # Point to base URL for git clone commands
    export GEOIPS_PACKAGES_DIR=$HOME/geoips
    export GEOIPS_TESTDATA_DIR=$GEOIPS_PACKAGES_DIR/test_data
    export GEOIPS_OUTDIRS=$GEOIPS_PACKAGES_DIR/outdirs

.. code:: bash

    echo "export GEOIPS_REPO_URL=$GEOIPS_REPO_URL" >> ~/.bashrc
    echo "export GEOIPS_PACKAGES_DIR=$GEOIPS_PACKAGES_DIR" >> ~/.bashrc
    echo "export GEOIPS_TESTDATA_DIR=$GEOIPS_TESTDATA_DIR" >> ~/.bashrc
    echo "export GEOIPS_OUTDIRS=$GEOIPS_OUTDIRS" >> ~/.bashrc

3. Create and activate a conda environment with some dependencies
-----------------------------------------------------------------

Next we'll create a conda environment named ``geoips`` that contains all system
requirements for GeoIPS. Many of these may already be installed on your system, but this
command will ensure that for everyone.

.. code:: bash

    conda create -y -n geoips -c conda-forge python=3.10 gcc gxx geos openblas imagemagick git git-lfs rclone
    conda activate geoips  # RUN EVERY TIME YOU WANT TO USE GEOIPS!
    git lfs install

**Note:** You will need to run ``conda activate geoips`` every time you want to
run or work on GeoIPS.


4. Clone the GeoIPS git repository
----------------------------------

.. code:: bash

    mkdir -p $GEOIPS_PACKAGES_DIR
    git lfs install
    git clone ${GEOIPS_REPO_URL}/geoips.git $GEOIPS_PACKAGES_DIR/geoips
    cd $GEOIPS_PACKAGES_DIR/geoips
    pip install .[doc,lint,test]

5. Test your installation
-------------------------

To test your installation you will call two scripts:

- ``base_install.sh`` will clone repositories containing test data.
- ``base_test.sh`` will run a few integration tests to ensure that your
  installation is working correctly.

.. code:: bash

    git lfs install
    cd $GEOIPS_PACKAGES_DIR/geoips
    # Download the test data
    ./tests/integration_tests/base_install.sh
    # Run integration tests
    ./tests/integration_tests/base_test.sh

6. Test output
--------------

For reference, the end of the output from the and base_test.sh command should
look something like below, indicating that none of the tests failed:

.. code:: bash

    Package: geoips_base
    Total run time: 82 seconds
    Number data types run: 3
    Number data types failed: 0