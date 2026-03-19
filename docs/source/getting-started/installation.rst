.. _installation:

Installation
############

Prerequisites
*************

Operating System:

- Linux (RedHat and Debian flavors officially supported)
- MacOS (Not officially supported)
- Windows with WSL2 (Not officially supported)

Python version 3.11 or higher. We recommend using `Mamba`_, `Miniconda`_, or
`Anaconda`_ to manage your python environment, but any Python 3.11+
installation should work. Please see the :ref:`system requirements
<system-requirements>` for more information.

Installing from Pypi
********************

The simplest way to install GeoIPS is using pip to install from PyPI.

.. code-block:: bash

   pip install geoips

If you have difficulty with pip installation, please see the
:ref:`troubleshooting <installation-troubleshooting>` section at the end of
this page.

Environment Setup
*****************
GeoIPS requires a minimum of two environment variables to be set. There are a
number of other environment variables that control other features of GeoIPS,
but ``GEOIPS_OUTDIRS`` and ``GEOIPS_TESTDATA_DIR`` are required.

``GEOIPS_OUTDIRS`` tells GeoIPS where it should store output files including
final products as well as cache files used to reduce recomputation of commonly
used variables like geostationary geolocation data.

``GEOIPS_TESTDATA_DIR`` tells GeoIPS where to download and look for test data.

It is important to choose a location that has sufficient space. Unfortunately,
"sufficient" differs based on your use case. Please see `system requirements
<system-requirements>`_ for more information.

.. code-block:: bash

   export GEOIPS_OUTDIRS=$HOME/geoips_output
   export GEOIPS_TESTDATA_DIR=$HOME/geoips_test_data
   mkdir -p $GEOIPS_OUTDIRS $GEOIPS_TESTDATA

.. tip::
    These environment variables can be persisted either by adding them to your
    shell environment (e.g. ``.bashrc``) or by adding them to your conda
    environment using ``conda env config vars set
    GEOIPS_OUTDIRS=$HOME/geoips_output``.

Testing Your Installation
*************************
There are a number of test datasets available for GeoIPS. The test below
downloads some calibrated level-1 data from GOES-18 ABI, then attempts to
produce an infrared imagery over the continental United States.

.. code-block:: bash

   geoips config install test_data_abi

   geoips run single_source \
       $GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b-RadF-M6C* \
       --reader_name abi_netcdf \
       --product_name Infrared \
       --output_formatter imagery_annotated \
       --sector_list conus

The end of the output should appear as below. The final line should display
``Return value: 0``.

.. code-block::

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

.. _installation-troubleshooting:

Troubleshooting
****************

The most common installation issue is caused by inconsistent libraries.
To resolve this, we recommend installing the following packages using conda
from the conda-forge channel:

- xarray
- netcdf4
- h5py
- pyhdf

.. code-block:: bash

   conda install -c conda-forge xarray netcdf4 h5py pyhdf

Other installation issues (e.g. dependency, architecture, or OS issues) may be
solved by cloning the GeoIPS git repository and installing from source.

.. code-block:: bash

    git clone https://github.com/NRLMMD-GEOIPS/geoips.git
    cd geoips
    pip install .

If you continue having difficulties, please open an issue on the `GEOIPS
GitHub repository <geoips_github_>`_.
