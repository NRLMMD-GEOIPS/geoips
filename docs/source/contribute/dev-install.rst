
.. _developer-installation:

Developer Installation
**********************

This guide is for developers who need the full GeoIPS development environment with source code access, testing capabilities, and all plugins.

**For the fully supported user installation with all dependencies managed automatically, use the** :ref:`Complete Local conda-based GeoIPS Installation<linux-installation>`.

System Dependencies
-------------------

Required system dependencies:

* Python >= 3.11
* git >= 2.19.1
* libopenblas-dev
* make
* g++ and gcc
* gfortran
* wget

Environment Variables
---------------------

Set these environment variables before installation:

.. code:: bash

    export GEOIPS_REPO_URL=https://github.com/NRLMMD-GEOIPS
    export GEOIPS_PACKAGES_DIR=<installation_location>
    export GEOIPS_TESTDATA_DIR=<desired_test_data_location>
    export GEOIPS_OUTDIRS=<desired_output_file_location>

Installation Steps
------------------

.. code:: bash

    # Clone the repository
    git clone $GEOIPS_REPO_URL/geoips.git $GEOIPS_PACKAGES_DIR/geoips
    
    # Install in editable mode
    pip install -e $GEOIPS_PACKAGES_DIR/geoips[doc,lint,test,debug]
    
    # Install additional plugins and test data
    $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/base_install.sh
    
    # Run tests to verify installation
    $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/base_test.sh

Plugin Installation Levels
---------------------------

Choose your installation level based on development needs:

* **Base**: Core plugins only (base_install.sh)
* **Full**: Extended plugin suite (base_install.sh + full_install.sh)
* **System**: Complete plugin suite (base_install.sh + full_install.sh + system_install.sh)

Docker Plugin Development Environment
=====================================

For containerized plugin development:

.. code:: bash

    # Pull the development image
    docker pull geoips/geoips:doclinttest-latest
    
    # Or build from source for specific stages
    docker build --target dev -t geoips:dev .
    docker build --target test_full -t geoips:test_full .
    docker build --target test_system -t geoips:test_system .

Available Docker stages:

* **build**: Base development environment
* **test_base**: Minimal testing environment
* **test_full**: Full testing environment with all plugins
* **test_system**: Complete testing environment
* **dev**: Full development environment with linting and debugging tools

Test Data Requirements
======================

Developers need test data repositories in $GEOIPS_TESTDATA_DIR for tests to pass. This is automatically handled by the installation scripts but requires significant disk space and download time.

**Important**: Test data is only required for development. Users installing via pip do not need test data.
