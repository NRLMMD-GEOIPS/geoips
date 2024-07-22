:orphan:

.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

Installing
==========

.. note::

    Setting up WSL through windows is the easiest method for running GeoIPS on
    a Windows system. To do so, follow directions on
    `Microsoft WSL Install <https://learn.microsoft.com/en-us/windows/wsl/install>`_.
    This requires administrator privileges.

For all installation methods, you need to setup environmental variables.

The required environmental variables are:

  -``GEOIPS_PACKAGES_DIR`` is where GeoIPS looks for itself and its plugin packages
  -``GEOIPS_TESTDATA_DIR`` is where GeoIPS looks to find its test datasets
  -``GEOIPS_OUTDIRS`` defines where GeoIPS will write output data and imagery

These are fine defaults for most users:

.. code:: bash

    export GEOIPS_PACKAGES_DIR=$HOME/geoips
    export GEOIPS_TESTDATA_DIR=$GEOIPS_PACKAGES_DIR/test_data
    export GEOIPS_OUTDIRS=$GEOIPS_PACKAGES_DIR/outdirs

If desired, the GeoIPS environment variables can be added to your
default shell configuration file (which is typically stored in
``$HOME/.bashrc``) by running the following commands or something similar:

.. code:: bash

    echo "export GEOIPS_PACKAGES_DIR=$GEOIPS_PACKAGES_DIR" >> ~/.bashrc
    echo "export GEOIPS_TESTDATA_DIR=$GEOIPS_TESTDATA_DIR" >> ~/.bashrc
    echo "export GEOIPS_OUTDIRS=$GEOIPS_OUTDIRS" >> ~/.bashrc

Install system dependencies directly
------------------------------------

If you are an expert user, you may want to install the dependencies manually. Do not do this if you already installed
dependencies with Conda.

Required
^^^^^^^^

* ``git``
* ``openblas`` (required for scipy pip install)
* ``make`` (required for pypublicdecompwt)
* ``python`` >= 3.9

Optional
^^^^^^^^

* ``gfortran`` (required for plugins including fortran builds)
* ``gcc`` and ``g++`` (required for plugins including fortran or C builds, and ARM machines)
* ``pdflatex`` (optional, for building pdf documentation)
* ``wget`` (required for downloading test data)
* ``make`` (optional, for building packages on ARM machines)
* Test data repos can be installed in `$GEOIPS_TESTDATA_DIR`

Debian
^^^^^^

For example, on Debian machines, you can install the optional and required dependencies like this:

.. code:: bash

    sudo apt-get install git make libopenblas-dev python3
    sudo apt-get install gfortran gcc g++ gdal-bin libgdal-dev texlive-latex-base wget make

This takes ~1gb of space.

Install GeoIPS
--------------

We can use ``pip`` to install all GeoIPS Python dependencies, and GeoIPS itself.

First, clone the GeoIPS git repository:

.. code:: bash

    git clone https://github.com/NRLMMD-GeoIPS/geoips.git $GEOIPS_PACKAGES_DIR/geoips

.. code:: bash

    # Ensure geoips python environment enabled before installing geoips
    pip install "$GEOIPS_PACKAGES_DIR/geoips"

If you want to install GeoIPS with all optional dependencies, you can use:

.. code:: bash

    # Ensure geoips python environment enabled before installing geoips
    pip install "$GEOIPS_PACKAGES_DIR/geoips[doc,lint,test,debug]"

The optional dependencies are:

- ``doc``: for building the documentation with Sphinx
  (the documentation is also available online at
  https://nrlmmd-geoips.github.io/geoips/)
- ``lint``: for linting the code (useful for developers)
- ``test``: for running the tests
- ``debug``: for debugging the code with IPython/jupyter

Development
-----------

The installation steps for developers are the same as for normal and/or expert users, except for one step.

Most developers use Conda installations, but any dependency management solution is fine.

When installing geoips, please install all the extras and install in **editable** mode so that changes to the code are
immediately reflected in the installed package. Eg.

.. code:: bash

    # Ensure geoips python environment enabled before installing geoips
    pip install -e "$GEOIPS_PACKAGES_DIR/geoips[doc,lint,test,debug]"

See the [ADDING FUNCTIONALITY] page for more details on how to contribute to GeoIPS.

Docker
------

We provide a working Dockerfile that can be used to run GeoIPS in a container.

The Dockerfile can be built into a Docker image by cloning the GeoIPS repository and
running ``docker build``. For example:

.. code:: bash

    git clone https://github.com/NRLMMD-GEOIPS/geoips.git geoips
    cd geoips
    docker build -t geoips .

The Docker image can be run with the following command:

.. code:: bash

    docker run -it geoips   # Run the container in interactive mode

Right now, the Docker image is only used for development and testing.

We suggest mounting in a data directory so your containers don't get too large.

If you are interested in using the Docker build
for production or plugin development, please reach
out to us via our contact page [CONTACT PAGE] or create an issue on GitHub [ISSUE PAGE].
