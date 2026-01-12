.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _dev-mac-installation:

Conda-based Installation for Mac
********************************

Using a fresh Mini/Anaconda Python 3.11+ Environment is the easiest way to
get geoips up and running.

Complete Local conda-based GeoIPS Installation
==============================================

The following instructions will guide you through installing GeoIPS using
Anaconda Python on Mac OSX. This installation method allows users to install
GeoIPS without requiring administrative privileges by using Conda to install all
of the "Required" system dependencies, then installing geoips into that conda
environment.

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
``$HOME/.bashrc`` or ``$HOME/.zshrc`` by running the following commands:

.. code:: bash

    echo "export GEOIPS_REPO_URL=$GEOIPS_REPO_URL" >> ~/.bashrc
    echo "export GEOIPS_PACKAGES_DIR=$GEOIPS_PACKAGES_DIR" >> ~/.bashrc
    echo "export GEOIPS_TESTDATA_DIR=$GEOIPS_TESTDATA_DIR" >> ~/.bashrc
    echo "export GEOIPS_OUTDIRS=$GEOIPS_OUTDIRS" >> ~/.bashrc

2. Install Anaconda or Miniconda
--------------------------------

- Download the appropriate version of `Conda
  <https://www.anaconda.com/download#downloads>`_,  `Miniconda
  <https://docs.conda.io/en/latest/miniconda.html>`_, or
  `Miniforge/Mambaforge <https://github.com/conda-forge/miniforge#download>`_.

.. code:: bash

    # Mamba for Intel chips
    curl -L -o conda_install.sh \
    https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh
    # Mamba for ARM (M1/M2) chips
    curl -L -o conda_install.sh \
    https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh
    # Anaconda for Intel chips
    curl -L -o conda_install.sh https://repo.anaconda.com/archive/Anaconda3-2023.07-2-MacOSX-x86_64.sh
    # Anaconda for ARM (M1/M2) chips
    curl -L -o conda_install.sh https://repo.anaconda.com/archive/Anaconda3-2023.07-2-MacOSX-arm64.sh
    # Miniconda for Intel chips
    curl -L -o conda_install.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
    # Miniconda for ARM (M1/M2) chips
    curl -L -o conda_install.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh

- Make the install script executable and run the installer,
  following the prompts (particularly the bit about
  conda init / restarting terminal!):

.. code:: bash

    chmod u+x conda_install.sh
    ./conda_install.sh
    # Follow instructions regarding conda init / restarting your terminal !

3. Create and activate a conda environment with some dependencies
-----------------------------------------------------------------

Next we'll create a conda environment named ``geoips`` that contains all system
requirements for GeoIPS. Many of these may already be installed on your system,
but this command will ensure that for everyone.

.. code:: bash

    # git required for pulling from git and for -C commands
    # pyhdf and pykdtree don't have wheels for mac and don't build cleanly
    #   best to install via conda
    conda create -y -n geoips -c conda-forge python=3.11 openblas git pyhdf pykdtree
    conda activate geoips  # RUN EVERY TIME YOU WANT TO USE GEOIPS!

**Note:** You will need to run ``conda activate geoips`` every time you want to
run or work on GeoIPS.

4. Clone the GeoIPS git repository, for installation and testing commands
-------------------------------------------------------------------------

.. code:: bash

    mkdir -p $GEOIPS_PACKAGES_DIR
    git clone ${GEOIPS_REPO_URL}/geoips.git $GEOIPS_PACKAGES_DIR/geoips

5. Install the GeoIPS git repository
------------------------------------

This command installs all GeoIPS Python dependencies, and GeoIPS itself.

.. code:: bash

    # Ensure geoips python environment enabled before installing geoips
    # using "conda activate geoips"

    # Install geoips via pip
    pip install -e "$GEOIPS_PACKAGES_DIR/geoips[doc,lint,test,debug]"

6. Test your installation
-------------------------

To test your installation you will call two scripts:

- ``base_install.sh`` will clone repositories containing test data.
- ``base_test.sh`` will run a few integration tests to ensure that your
  installation is working correctly.

.. code:: bash

    # Ensure geoips python environment enabled
    # using "conda activate geoips"

    # Download the test data
    $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/base_install.sh

    # Create the GeoIPS plugin registries
    geoips config create-registries

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

