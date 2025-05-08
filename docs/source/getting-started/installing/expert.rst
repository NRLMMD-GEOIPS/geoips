.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _expert-installation:

Expert User Installation (with administrative privileges)
*********************************************************

The :ref:`Complete Local conda-based GeoIPS Installation<linux-installation>`
is the easiest way to get GeoIPS up and running, but if you have administrative
privileges on your system, and are confident you can install all the required
system dependencies yourself, you can install GeoIPS by setting a few environment
variables for testing purposes.

Expert User GeoIPS Installation
===============================

System Dependencies
-------------------

**Use the** :ref:`Complete Local conda-based GeoIPS Installation<linux-installation>`
**for the fully supported installation, which includes all
dependencies**

Required (**included in**
:ref:`Complete Local conda-based GeoIPS Installation<linux-installation>`)

* wget (Miniconda installation)
* git >= 2.19.1 (git -C commands in complete installation)
* openblas (required for scipy pip install)
* make (required for pypublicdecompwt)
* Python >= 3.11.0 (3.11.0 required for entry points)
* Test data repos contained in $GEOIPS_TESTDATA_DIR
  (required for tests to pass)
* pdflatex (optional, for building pdf documentation)
  (required for tests to pass)

Optional

* gfortran (only required for plugins including fortran builds, build-essential)
* gcc & g++ (required for plugins including fortran or C builds, build-essential)
* screen (convenience package)
* ncurses (only required if building vim, ncurses and libncurses5-dev)

Minimal install
---------------

**Use the** :ref:`Complete Local conda-based GeoIPS Installation<linux-installation>`.
**for the fully supported installation, which includes all
dependencies**

If you are confident you have all system requirements installed
(Python+cartopy), and do not wish to go through the full
installation process (which includes conda, rclone, test data, etc),
you can clone the geoips repo and pip install from your local copy.

**For the fully supported installation, please use the**
:ref:`Complete Local conda-based GeoIPS Installation<linux-installation>`.

.. code:: bash

    # NOTE: ALL dependencies above MUST be installed/available
    #       to use this installation method.
    # Please follow complete conda-based installation in the
    #       next section for fully supported complete install.
    export GEOIPS_REPO_URL=https://github.com/NRLMMD-GEOIPS
    export GEOIPS_PACKAGES_DIR=<installation_location>
    export GEOIPS_TESTDATA_DIR=<desired_test_data_location>
    export GEOIPS_OUTDIRS=<desired_output_file_location>

    git clone $GEOIPS_REPO_URL/geoips.git $GEOIPS_PACKAGES_DIR/geoips
    pip install -e $GEOIPS_PACKAGES_DIR/geoips
    $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/base_install.sh
    $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/base_test.sh
