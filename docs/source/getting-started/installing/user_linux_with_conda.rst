.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _linux-installation:

Installation on Linux
*********************

This page provides instructions for installing GeoIPS using wheels from PyPI in a
conda virtual environment. This installation method is recommended for users with
or without administrative privleges.

Developers of core GeoIPS should follow the appropriate guide under "Contribute".

1. Install Anaconda or Miniconda
--------------------------------

Use a fresh Miniconda or Anaconda environment with **Python 3.11 or later**.

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


- Create a conda environment named, for example, ``geoips`` with the appropriate
  dependencies:

  .. code:: bash

      mamba create -y -n geoips -c conda-forge python=3.11 openblas git
      conda activate geoips  # RUN EVERY TIME YOU WANT TO USE GEOIPS!

.. note::

   You must run ``conda activate geoips``
   every time you run or work with GeoIPS.

2. Install GeoIPS using pip
---------------------------

Once inside the `geoips` environment, install GeoIPS from PyPI:

.. code:: bash

    pip install geoips

3. Test Data Setup
------------------

GeoIPS test data download requires the following environment variables to be set:

.. code:: bash

    conda env config vars set GEOIPS_PACKAGES_DIR=$HOME/geoips
    # Reactivate environment for variables to take effect
    conda deactivate && conda activate geoips
    conda env config vars set GEOIPS_TESTDATA_DIR=$GEOIPS_PACKAGES_DIR/test_data
    conda env config vars set GEOIPS_OUTDIRS=$GEOIPS_PACKAGES_DIR/outdirs
    conda deactivate && conda activate geoips
    mkdir -p "$GEOIPS_PACKAGES_DIR" "$GEOIPS_TESTDATA_DIR" "$GEOIPS_OUTDIRS"

.. note::

   You can customize test data location
   by changing the value of ``GEOIPS_TESTDATA_DIR``.

4. Run a Sample Script
----------------------

Download the sample dataset using geoips CLI command:

.. code:: bash

    geoips config install test_data_abi

Test the installation by running a sample GeoIPS processing script.

.. code:: bash

    geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b-RadF-M6C* \
    --reader_name abi_netcdf \
    --product_name Infrared \
    --output_formatter imagery_annotated \
    --sector_list conus

The end of the output from the above script should resemble the example below, showing
the path to the generated output image. The final line should display `Return value: 0`,
indicating that the script ran successfully.

.. code:: bash

    # Truncated log output from the script run
    .......
    11_191109    log_setup.py:162  INTERACTIVE: SINGLESOURCESUCCESS ${GEOIPS_OUTDIRS}/preprocessed/annotated_imagery/NorthAmerica-UnitedStates-Continental/x-x-x/Infrared/abi/20200918.195020.goes-16.abi.Infrared.conus.97p12.noaa.3p0.png
    11_191109    log_setup.py:162  INTERACTIVE: READER_NAME: abi_netcdf
    11_191109    log_setup.py:162  INTERACTIVE: PRODUCT_NAME: Infrared
    11_191109    log_setup.py:162  INTERACTIVE: NUM_PRODUCTS: 1
    11_191109    log_setup.py:162  INTERACTIVE: NUM_DELETED_PRODUCTS: 0
    11_191109    log_setup.py:162  INTERACTIVE: Completed geoips PROCFLOW single_source processing, done!
    11_191109    log_setup.py:162  INTERACTIVE: Total time: 0:00:24.911853
    11_191109    log_setup.py:162  INTERACTIVE: Return value: 0
