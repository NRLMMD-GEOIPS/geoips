.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _user-installation:

User Installation
*****************

This guide is for users who want to install GeoIPS. For development work, see the Contribute section.

**For the fully supported installation with all dependencies managed automatically, use the** :ref:`Complete Local conda-based GeoIPS Installation<linux-installation>`.

PyPI Installation
=================

The simplest way to install GeoIPS is via pip:

.. code:: bash

    pip install geoips

This installs the core GeoIPS package with basic functionality.

System Dependencies
-------------------

GeoIPS requires Python >= 3.11. Most other dependencies are handled automatically by pip, but you may need to install these system packages depending on your use case:

Optional system dependencies:

* libopenblas-dev (for enhanced performance with scipy)
* make (required for some optional features)

Environment Variables
---------------------

Set this environment variable for output files:

.. code:: bash

    export GEOIPS_OUTDIRS=<desired_output_file_location>

Docker Installation
===================

A Docker image is available for both users and developers:

.. code:: bash

    docker pull geoips/geoips:doclinttest-latest

Note: The current public image builds to a development stage. For production use, you may need to build a custom image from the provided Dockerfile.

WARNING: The current dockerfile is in development, please expect it to have breaking changes.

Plugin Levels
=============

The GeoIPS Dockerfile supports different plugin levels:

* **Base**: Core functionality (included with pip install)
* **Full**: Additional plugins for extended capabilities
* **System**: Complete plugin suite

The pip installation provides the base level. Additional plugins require separate installation or the developer setup.
