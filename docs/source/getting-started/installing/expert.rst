.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _user-installation:

Expert User Installation
************************

This guide is for users who want to install GeoIPS. For development work, see the Contribute section.

**For the fully supported installation with all dependencies managed
automatically, use the** :ref:`Complete Local conda-based GeoIPS
Installation<linux-installation>`.

PyPI Installation
=================

The simplest way to install GeoIPS is via pip:

.. code:: bash

    pip install geoips

This installs the core GeoIPS package with basic functionality.

System Dependencies
-------------------

GeoIPS requires Python >= 3.11. Most other dependencies are handled
automatically by pip, but you may need to install these system packages
depending on your use case:

Optional system dependencies:

* libopenblas-dev (for enhanced performance with scipy)
* make (required for some optional features)

Environment Variables
---------------------

Set this environment variable for output files:

.. code:: bash

    export GEOIPS_OUTDIRS=<desired_output_file_location>

Nix Installation
================

The repository ships a `Nix flake <https://nixos.wiki/wiki/Flakes>`_ that
provides a reproducible development shell. The shell includes Python 3.12
together with the native libraries the scientific stack links against (PROJ,
GEOS, HDF5, netCDF, HDF4, ecCodes, and OpenBLAS), so you do not have to install
those system packages yourself.

Clone the repository and enter the shell:

.. code:: bash

    git clone https://github.com/NRLMMD-GEOIPS/geoips.git
    cd geoips
    nix develop

On first entry the flake creates an isolated environment and installs GeoIPS
from the checkout, leaving you in a shell where the ``geoips`` command is ready
to use:

.. code:: bash

    geoips --help

To use the shell without cloning first:

.. code:: bash

    nix develop github:NRLMMD-GEOIPS/geoips

This requires Nix with `flakes enabled
<https://nixos.wiki/wiki/Flakes#Enable_flakes_permanently_in_NixOS>`_.

Docker Installation
===================

A Docker image is available for both users and developers:

.. code:: bash

    docker pull geoips/geoips:doclinttest-latest

Note: The current public image builds to a development stage. For production
use, you may need to build a custom image from the provided Dockerfile.

WARNING: The current dockerfile is in development, please expect it to have
breaking changes.

Plugin Levels
=============

The GeoIPS Dockerfile supports different plugin levels:

* **Base**: Core functionality (included with pip install)
* **Full**: Additional plugins for extended capabilities
* **System**: Complete plugin suite

The pip installation provides the base level. Additional plugins require separate installation or the developer setup.
