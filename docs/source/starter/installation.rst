.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _linux-installation:

Conda-based Installation for Linux
**********************************

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
    # Point to base URL for git clone commands
    export GEOIPS_REPO_URL=https://github.com/NRLMMD-GeoIPS
    export GEOIPS_PACKAGES_DIR=$HOME/geoips
    export GEOIPS_TESTDATA_DIR=$GEOIPS_PACKAGES_DIR/test_data
    export GEOIPS_OUTDIRS=$GEOIPS_PACKAGES_DIR/outdirs
    # Clone the GeoIPS git repository, for installation and testing setup
    mkdir -p $GEOIPS_PACKAGES_DIR
    git clone ${GEOIPS_REPO_URL}/geoips.git $GEOIPS_PACKAGES_DIR/geoips

If desired, the GeoIPS environment variables can be added to your
``$HOME/.bashrc`` by running the following commands:

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

  For example, for Linux with Intel chips, one of the following:

  .. code:: bash

      # wget https://repo.anaconda.com/archive/Anaconda3-2023.03-1-Linux-x86_64.sh
      # wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
      # wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
      wget https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh

- Make the installation script executable, and run the installer.
  - Accept the license terms and cofirm the location.
  - Follow any additional instructions provided by the installer.

  .. code:: bash

      chmod u+x ./Mambaforge-Linux-x86_64.sh
      # No terminal reconnection is required afterward.
      # Make sure you set env vars again if you restart your terminal !
      ./Mambaforge-Linux-x86_64.sh


  .. code:: bash

      # Clean up after yourself
      rm -f ./Mambaforge-Linux-x86_64.sh

3. Create and activate a conda environment with some dependencies
-----------------------------------------------------------------

Next we'll create a conda environment named ``geoips`` that contains all system
requirements for GeoIPS. Many of these may already be installed on your system,
but this command will ensure that for everyone.

.. code:: bash

    # Note geos no longer required for cartopy >= 0.22
    # openblas / gcc required for recenter_tc / akima build.
    # git required for -C commands
    mamba create -y -n geoips -c conda-forge python=3.10 gcc gxx openblas git
    conda activate geoips  # RUN EVERY TIME YOU WANT TO USE GEOIPS!

**Note:** You will need to run ``conda activate geoips``
every time you want to run or work on GeoIPS.

4. Install the GeoIPS git repository
------------------------------------

This command installs all GeoIPS Python dependencies, and GeoIPS itself.

.. code:: bash

    # Ensure geoips python environment enabled before installing geoips
    pip install -e "$GEOIPS_PACKAGES_DIR/geoips[doc,lint,test,debug]"

5. Test your installation
-------------------------

To test your installation you will need to download test data,
and run integration tests:

- ``base_install.sh`` will clone repositories containing test data.
- ``create_plugin_registries`` will identify and register all available plugins
  from all geoips plugin packages, for run-time execution.
- ``base_test.sh`` will run a few integration tests to ensure that your
  installation is working correctly.

.. code:: bash

    # Ensure geoips python environment enabled

    $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/base_install.sh

    # Create the GeoIPS plugin registries
    create_plugin_registries

    # Run integration tests
    $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/base_test.sh

6. Test output
--------------

For reference, the end of the output from the base_test.sh command should
look something like below, indicating that none of the tests failed:

.. code:: bash

    Package: geoips_base
    Total run time: 82 seconds
    Number data types run: 3
    Number data types failed: 0

7. OPTIONAL: Capture working requirements.txt for base install
--------------------------------------------------------------

OPTIONAL: These can be commited to the repository for reference - only commit if
base_test.sh returns 0!  Not required.

.. code:: bash

  if [[ "$NEW_GEOIPS_VERSION" != "" ]]; then
      GEOIPS_VERS=$NEW_GEOIPS_VERSION
  fi
  if [[ "$GEOIPS_VERS" == "" ]]; then
      GEOIPS_VERS=`python -c "import geoips; print(geoips.__version__)"`
  fi

  mkdir -p $GEOIPS_PACKAGES_DIR/geoips/environments

  $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh dump_pip_environment \
    $GEOIPS_PACKAGES_DIR/geoips/environments/pip_base_requirements_${GEOIPS_VERS}_`date -u +%Y%m%d`.txt

  $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh dump_mamba_environment \
    $GEOIPS_PACKAGES_DIR/geoips/environments/mamba_base_package_list_${GEOIPS_VERS}_`date -u +%Y%m%d`.yml
