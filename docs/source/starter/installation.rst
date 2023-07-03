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

************************
Conda-based Installation
************************

Using a fresh Mini/Anaconda Python 3.9+ Environment is the easiest way to
get geoips up and running.

Complete Local conda-based GeoIPS Installation
==============================================

The following instructions will guide you through installing GeoIPS using
Anaconda Python. This installation method allows users to install GeoIPS without
requiring administrative privileges by using Conda to install all of the
"Required" system dependencies, then installing geoips into
that conda environment.

1. Set GeoIPS Environment Variables
-----------------------------------

In order to support GeoIPS' testing infrastructure, there are a few required
environment variables.
You can change your installation location by changing the value of
``$GEOIPS_PACKAGES_DIR`` below.

.. code:: bash

    # GeoIPS Default Locations
    export GEOIPS_REPO_URL=https://github.com/NRLMMD-GeoIPS  # Point to base URL for git clone commands
    export GEOIPS_PACKAGES_DIR=$HOME/geoips
    export GEOIPS_TESTDATA_DIR=$GEOIPS_PACKAGES_DIR/test_data
    export GEOIPS_OUTDIRS=$GEOIPS_PACKAGES_DIR/outdirs

If desired, the GeoIPS environment variables can be added to your
``$HOME/.bashrc`` by running the following commands:

.. code:: bash

    echo "export GEOIPS_REPO_URL=$GEOIPS_REPO_URL" >> ~/.bashrc
    echo "export GEOIPS_PACKAGES_DIR=$GEOIPS_PACKAGES_DIR" >> ~/.bashrc
    echo "export GEOIPS_TESTDATA_DIR=$GEOIPS_TESTDATA_DIR" >> ~/.bashrc
    echo "export GEOIPS_OUTDIRS=$GEOIPS_OUTDIRS" >> ~/.bashrc

2. Clone the GeoIPS git repository, for installation and testing commands
-------------------------------------------------------------------------

.. code:: bash

    mkdir -p $GEOIPS_PACKAGES_DIR
    git clone ${GEOIPS_REPO_URL}/geoips.git $GEOIPS_PACKAGES_DIR/geoips

3. Install Anaconda or Miniconda
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

4. Create and activate a conda environment with some dependencies
-----------------------------------------------------------------

Next we'll create a conda environment named ``geoips`` that contains all system
requirements for GeoIPS. Many of these may already be installed on your system,
but this command will ensure that for everyone.


.. code:: bash

    conda create -y -n geoips -c conda-forge python=3.10 gcc gxx geos openblas imagemagick git git-lfs rclone
    conda activate geoips  # RUN EVERY TIME YOU WANT TO USE GEOIPS!
    git lfs install

**Note:** You will need to run ``conda activate geoips`` every time you want to
run or work on GeoIPS.

5. Install the GeoIPS git repository
------------------------------------

This command installs all GeoIPS Python dependencies, and GeoIPS itself.

.. code:: bash

    # Ensure geoips python environment enabled before installing geoips
    pip install -e "$GEOIPS_PACKAGES_DIR/geoips"[doc,lint,test]

6. Test your installation
-------------------------

To test your installation you will call two scripts:

- ``base_install.sh`` will clone repositories containing test data.
- ``base_test.sh`` will run a few integration tests to ensure that your
  installation is working correctly.

.. code:: bash

    # Ensure geoips python environment enabled
    # Ensure git lfs is enabled BEFORE attempting to download data
    git lfs install
    # Download the test data
    $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/base_install.sh
    # Run integration tests
    $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/base_test.sh

7. Test output
--------------

For reference, the end of the output from the base_test.sh command should
look something like below, indicating that none of the tests failed:

.. code:: bash

    Package: geoips_base
    Total run time: 82 seconds
    Number data types run: 3
    Number data types failed: 0
