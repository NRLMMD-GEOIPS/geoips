.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
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
      wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh

- Make the install script executable and run the installer,
  following the prompts (particularly the bit about
  conda init / restarting terminal!):

  .. code:: bash

      chmod u+x ./Miniforge3-Linux-x86_64.sh
      # After installing, follow instructions regarding conda init / restarting your terminal !
      # Make sure you set env vars again if you restart your terminal !
      ./Miniforge3-Linux-x86_64.sh

  .. code:: bash

      # Clean up after yourself
      rm -f ./Miniforge3-Linux-x86_64.sh

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
- ``test_installation.py`` will run a few integration tests to ensure that your
  installation is working correctly. For more information on running test_installation.py
  please see https://github.com/NRLMMD-GEOIPS/geoips/blob/942ef8e7d66a163fa7feba9e1f17a95d3ba83b63/docs/dev/integration_tests.rst#L114

.. code:: bash

    # Ensure geoips python environment enabled

    # Install base GeoIPS package and minimal test datasets.
    $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/base_install.sh

    # Create the GeoIPS plugin registries
    create_plugin_registries

    # Run integration tests
    pytest -m "integration and base"

6. Test output
--------------

- **Successful Run**:
  If all tests pass, `pytest` will report a summary at the end indicating
  success (e.g, `== 53 passed in 30.00m ==`).

- **Failures**:
  If any script fails, `pytest` will display a traceback and the relevant
  command output. Since these scripts are run via bash, a `CalledProcessError`
  may be raised if the shell command returns a non-zero exit code. In such
  cases, review the error output to determine what went wrong, fix the
  underlying issue (or ask for help), and rerun the tests.

- **Debugging Failed Tests**:
  Consider running the failed script directly in a terminal to isolate the
  problem. For example, if a test script
  `"$geoips_repopath/tests/scripts/abi.config_based_output.sh"` fails, try
  running it separately:

  .. code-block:: bash

      cd $geoips_repopath
      bash tests/scripts/abi.config_based_output.sh

  This can help you identify environment issues, missing dependencies, or
  other runtime problems.

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
