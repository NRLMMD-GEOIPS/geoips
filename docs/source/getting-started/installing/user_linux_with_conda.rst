.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _linux-installation:

This page provides instructions for installing GeoIPS using wheels from PyPI in a
virtual environment. This installation method is recommended for users who do not
intend to modify the source code.

**System-level prerequisite** : ``wget``

1. Install Anaconda or Miniconda
--------------------------------

The following instructions create a virtual environment for installing GeoIPS. This
approach enables users to install GeoIPS without requiring administrative privileges by
using Conda to manage all required system dependencies

Using a fresh Miniconda or Anaconda environment with **Python 3.11 or later** is the recommended
setup to get Geoips up and running.

- Download the appropriate version of `Conda
  <https://www.anaconda.com/download#downloads>`_,  `Miniconda
  <https://docs.conda.io/en/latest/miniconda.html>`_, or
  `Miniforge/Mambaforge <https://github.com/conda-forge/miniforge#download>`_.

  For example, for Linux with Intel chips, one of the following:

  .. code:: bash

      # wget https://repo.anaconda.com/archive/Anaconda3-2023.03-1-Linux-x86_64.sh
      # wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
      wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh

- Make the installer script executable and run it, following the prompts (particularly the bit about
  conda init / restarting terminal!):

  .. code:: bash

      chmod u+x ./Miniforge3-Linux-x86_64.sh
      # After installing, follow instructions regarding conda init / restarting your terminal !
      # Make sure you set env vars again if you restart your terminal !
      ./Miniforge3-Linux-x86_64.sh

  .. code:: bash

      # Clean up after yourself
      rm -f ./Miniforge3-Linux-x86_64.sh


- Create a conda environment named ``geoips`` that contains all system
  requirements for GeoIPS. Many of these may already be installed on your system,
  but this command will ensure that for everyone.

  .. code:: bash

      # Note geos no longer required for cartopy >= 0.22
      # openblas / gcc required for recenter_tc / akima build.
      # git required for -C commands
      # libgit2 sometimes required for brassy
      mamba create -y -n geoips -c conda-forge python=3.11 gcc gxx openblas git libgit2
      conda activate geoips  # RUN EVERY TIME YOU WANT TO USE GEOIPS!

  **Note:** You will need to run ``conda activate geoips``
  every time you want to run or work on GeoIPS.

2. Install GeoIPS using pip
---------------------------

Once inside the `geoips` environment, install GeoIPS from PyPI:

.. code:: bash

    pip install geoips
    pip list | grep "geoips"  # verify that GeoIPS is installed and check its version

3. Run A Script
---------------

Running a sample script to test your installation requires downloading test data.

GeoIPS test data download requires the following environment variables to be set:
You can customize test data location by changing the value of ``$GEOIPS_PACKAGES_DIR``.

.. code:: bash

    # set the required environment variables
    export GEOIPS_PACKAGES_DIR=$HOME/geoips
    export GEOIPS_TESTDATA_DIR=GEOIPS_PACKAGES_DIR/test_data

    # create required directories
    mkdir -p $GEOIPS_PACKAGES_DIR
    mkdir -p $GEOIPS_TESTDATA_DIR

    # install the test dataset
    geoips config install test_data_noaa_aws

If desired, the GeoIPS environment variables can be added to your
``$HOME/.bashrc`` by running the following commands:

.. code:: bash

    echo "export GEOIPS_PACKAGES_DIR=$GEOIPS_PACKAGES_DIR" >> ~/.bashrc
    echo "export GEOIPS_TESTDATA_DIR=$GEOIPS_TESTDATA_DIR" >> ~/.bashrc

Run the script

