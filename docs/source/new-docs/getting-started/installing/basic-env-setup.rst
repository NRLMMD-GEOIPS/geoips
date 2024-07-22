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

  - ``GEOIPS_PACKAGES_DIR`` is where GeoIPS looks for itself and its plugin packages
  - ``GEOIPS_TESTDATA_DIR`` is where GeoIPS looks to find its test datasets
  - ``GEOIPS_OUTDIRS`` defines where GeoIPS will write output data and imagery

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

Install Dependencies with Conda
-------------------------------

Conda is a package and virtual environment manager that can
be used to install the dependencies of GeoIPS.

We recommend using Conda if you are new to GeoIPS, programming or Python.

If you are an expert user, you may want to use the manual
or Docker installation methods.

Get Conda
^^^^^^^^^

- Download the appropriate version of `Conda
  <https://www.anaconda.com/download#downloads>`_,  `Miniconda
  <https://docs.conda.io/en/latest/miniconda.html>`_, or
  `Miniforge/Mambaforge <https://github.com/conda-forge/miniforge#download>`_.

  For example, for Linux with Intel chips, one of the following might work:

  .. code:: bash

      wget https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh

  To find your specific version, visit the `Miniforge/Mambaforge github page
  <https://github.com/conda-forge/miniforge/releases/>`_.

- Make the install script executable and run the installer,
  following the prompts. Eg.:

  .. code:: bash

      chmod u+x ./Mambaforge-Linux-x86_64.sh
      # After installing, follow instructions regarding conda init / restarting your terminal !
      # Make sure you set env vars again if you restart your terminal !
      ./Mambaforge-Linux-x86_64.sh

  .. code:: bash

      rm -f ./Mambaforge-Linux-x86_64.sh

Create and activate a conda environment with dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Next we'll create a conda environment named ``geoips`` that contains all system
requirements for GeoIPS.

.. code:: bash

    mamba create -y -n geoips -c conda-forge python=3.10 openblas git gfortran

.. warning::

        If you are using an ARM machine, you may need to install ``pyhdf`` with conda.
        If you run into ``fatal error: 'hdf.h' file not found`` when installing ``pyhdf``,
        you may need to install ``pyhdf`` with conda. You can do this with the following command:

        .. code:: bash

            mamba create -y -n geoips -c conda-forge python=3.10 openblas git gfortran **pyhdf**

Activate the conda environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You will need to run ``conda activate geoips`` (or ``mamba activate geoips``)
every time you want to run or work on GeoIPS. Eg.

.. code:: bash

    conda activate geoips

Install GeoIPS
--------------

We can use ``pip`` to install all GeoIPS Python dependencies, tests for GeoIPS and GeoIPS itself.

First, clone the GeoIPS git repository:

.. code:: bash

    git clone https://github.com/NRLMMD-GeoIPS/geoips.git $GEOIPS_PACKAGES_DIR/geoips

.. code:: bash

    # Ensure geoips python environment enabled before installing geoips
    pip install -e "$GEOIPS_PACKAGES_DIR/geoips[test]"

If you want to install GeoIPS with all optional dependencies, you can use:

.. code:: bash

    # Ensure geoips python environment enabled before installing geoips
    pip install -e "$GEOIPS_PACKAGES_DIR/geoips[doc,lint,test,debug]"

The optional dependencies are:

- ``doc``: for building the documentation with Sphinx
  (the documentation is also available online at
  https://nrlmmd-geoips.github.io/geoips/)
- ``lint``: for linting the code (useful for developers)
- ``test``: for running the tests
- ``debug``: for debugging the code with IPython/jupyter (also useful for developers)
