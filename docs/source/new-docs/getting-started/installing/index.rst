:orphan:

Installing
==========

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
``$HOME/.bashrc`` by running the following commands:

.. code:: bash

    echo "export GEOIPS_PACKAGES_DIR=$GEOIPS_PACKAGES_DIR" >> ~/.bashrc
    echo "export GEOIPS_TESTDATA_DIR=$GEOIPS_TESTDATA_DIR" >> ~/.bashrc
    echo "export GEOIPS_OUTDIRS=$GEOIPS_OUTDIRS" >> ~/.bashrc

Conda
-----

Install Conda
^^^^^^^^^^^^^

- Download the appropriate version of `Conda
  <https://www.anaconda.com/download#downloads>`_,  `Miniconda
  <https://docs.conda.io/en/latest/miniconda.html>`_, or
  `Miniforge/Mambaforge <https://github.com/conda-forge/miniforge#download>`_.

  For example, for Linux with Intel chips, one of the following:

  .. code:: bash

      # wget https://repo.anaconda.com/archive/Anaconda3-2023.03-1-Linux-x86_64.sh
      # wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
      # wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
      wget https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh

- Make the install script executable and run the installer,
  following the prompts (particularly the bit about
  conda init / restarting terminal!):

  .. code:: bash

      chmod u+x ./Mambaforge-Linux-x86_64.sh
      # After installing, follow instructions regarding conda init / restarting your terminal !
      # Make sure you set env vars again if you restart your terminal !
      ./Mambaforge-Linux-x86_64.sh

  .. code:: bash

      # Clean up after yourself
      rm -f ./Mambaforge-Linux-x86_64.sh

Create and activate a conda environment with dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Next we'll create a conda environment named ``geoips`` that contains all system
requirements for GeoIPS. Many of these may already be installed on your system,
but this command will ensure that for everyone.

.. code:: bash

    # Note geos no longer required for cartopy >= 0.22
    # openblas / gcc required for recenter_tc / akima build.
    # git required for -C commands
    mamba create -y -n geoips -c conda-forge python=3.10 gcc gxx openblas git
    mamba activate geoips  # RUN EVERY TIME YOU WANT TO USE GEOIPS!

.. note::
    You will need to run ``mamba activate geoips`` every time you want to run or work on GeoIPS.

Install the GeoIPS git repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Installs all GeoIPS Python dependencies, and GeoIPS itself.

.. code:: bash

    # Ensure geoips python environment enabled before installing geoips
    pip install -e "$GEOIPS_PACKAGES_DIR/geoips[doc,lint,test,debug]"

Expert
------

Development
-----------

Docker
------
