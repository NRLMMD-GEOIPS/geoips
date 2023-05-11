 | # # # Distribution Statement A. Approved for public release. Distribution unlimited.
 | # # #
 | # # # Author:
 | # # # Naval Research Laboratory, Marine Meteorology Division
 | # # #
 | # # # This program is free software: you can redistribute it and/or modify it under
 | # # # the terms of the NRLMMD License included with this program. This program is
 | # # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
 | # # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
 | # # # for more details. If you did not receive the license, for more information see:
 | # # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

************
Installation
************

Simple, Conda-based Installation
================================

The following instructions will guide you through installing GeoIPS using Anaconda
Python. This installation method allows users to install GeoIPS without requiring
administrative privileges by using Conda to install many of the required system
packages.

1. Install Anaconda or Miniconda
--------------------------------

For most situations, we recommend installing Anaconda Python or Miniconda, then
instal/home/jsolbrig/geoips/github/geoips_clavrxling GeoIPS and all of its dependencies
into a Conda environment.

- Download the appropriate version of `Conda
  <https://www.anaconda.com/download#downloads>`_ or `Miniconda
  <https://docs.conda.io/en/latest/miniconda.html>`_.

  For example, for Linux with Intel chips:
  .. code:: bash

      wget https://repo.anaconda.com/archive/Anaconda3-2023.03-1-Linux-x86_64.sh

- Make the install script executable:
  .. code:: bash

      chmod u+x Anaconda3-2023.03-1-Linux-x86_64.sh

- Run the installer and follow the prompts:
  .. code:: bash

      ./Anaconda3-2023.03-1-Linux-x86_64.sh

- Restart your terminal session

2. Add environment variables to ``$HOME/.bashrc``
-------------------------------------------------

Choose a location where you would like to install GeoIPS and its plugin packages. For
example, ``$HOME/geoips``. Then add the following lines to your ``$HOME/.bashrc`` file.

.. code:: bash

    export GEOIPS_REPO_URL=https://github.com/NRLMMD-GEOIPS
    export GEOIPS_PACKAGES_DIR=<path_where_you_want_to_install>
    export GEOIPS_OUTDIRS=$GEOIPS_PACKAGES_DIR/outdirs
    export GEOIPS_TESTDATA_DIR=$GEOIPS_PACKAGES_DIR/test_data

**Restart your terminal**

3. Create and activate a conda environment with some dependencies
-----------------------------------------------------------------

Next we'll create a conda environment named ``geoips`` that contains all system
requirements for GeoIPS. Many of these may already be installed on your system, but this
command will ensure that for everyone.

.. code:: bash

    conda create -y -n geoips -c conda-forge python=3.10 gcc gxx geos openblas imagemagick git git-lfs rclone
    conda activate geoips
    git lfs install

**Note:** You will need to run ``conda activate geoips`` every time you want to run or
work on GeoIPS.

4. Clone the GeoIPS git repository and its test data repositories
-----------------------------------------------------------------

.. code:: bash

    mkdir -p $GEOIPS_PACKAGES_DIR
    git clone ${GEOIPS_REPO_URL}/geoips.git $GEOIPS_PACKAGES_DIR/geoips
    cd $GEOIPS_PACKAGES_DIR/geoips
    pip install .[doc,lint,test]

5. Test your installation
-------------------------

To test your installation you will call two scripts: one to clone some repositories
containing test data and one to run a few integration tests.

.. code:: bash

    cd $GEOIPS_PACKAGES_DIR/geoips
    # Download the test data
    .tests/integration_tests/base_install.sh
    # Run integration tests
    ./tests/integration_tests/base_test.sh

Output should look like this:

.. code:: bash

    $> .tests/integration_tests/base_install.sh
    SUCCESS: 'git lfs install' appears to be installed successfully
        /root/micromamba/envs/geoips/bin/git

    SUCCESS: 'imagemagick' appears to be installed successfully
        /root/micromamba/envs/geoips/bin/compare

    SUCCESS: 'wget' appears to be installed successfully
        /usr/bin/wget

    SUCCESS: 'git' appears to be installed successfully
        /root/micromamba/envs/geoips/bin/git

    SUCCESS: 'python' appears to be installed successfully
        /root/micromamba/envs/geoips/bin/python

    SUCCESS: 'scipy/openblas' appear to be installed successfully

    SUCCESS: 'cartopy/libgeos' appear to be installed successfully

    SUCCESS: 'rclone' appears to be installed successfully
        /root/micromamba/envs/geoips/bin/rclone

    Updated Git hooks.
    Git LFS initialized.

    **Cloning, updating, and uncompressing test_data_amsr2.git

    **Cloning test_data_amsr2.git
    Cloning into '/root/geoips/test_data/test_data_amsr2'...
    remote: Enumerating objects: 58, done.
    remote: Counting objects: 100% (22/22), done.
    remote: Compressing objects: 100% (18/18), done.
    remote: Total 58 (delta 7), reused 14 (delta 3), pack-reused 36
    Receiving objects: 100% (58/58), 20.86 KiB | 2.32 MiB/s, done.
    Resolving deltas: 100% (14/14), done.
    Filtering content: 100% (8/8), 334.90 MiB | 44.76 MiB/s, done.
    git clone return: 0

    **Updating test repo test_data_amsr2 branch main
    Already up to date.
    fatal: a branch named 'main' already exists
    Already on 'main'
    Your branch is up to date with 'origin/main'.
    Already up to date.
    Already up to date.
    git checkout -t return: 128
    git checkout return: 0
    git pull return: 0
    **You can ignore 'fatal: A branch named <branch> already exists' - just means you already have the branch

    Attempting uncompress test_data_amsr2...
         /root/geoips/test_data/test_data_amsr2/uncompress_test_data.sh...
    Checking for tgz files in /root/geoips/test_data/test_data_amsr2/bg_data//*.tgz...
    Thu May 11 19:06:00 UTC 2023
       Trying /root/geoips/test_data/test_data_amsr2/bg_data//ahi_20200518_0740.tgz...
        tar -xzf /root/geoips/test_data/test_data_amsr2/bg_data//ahi_20200518_0740.tgz -C /root/geoips/test_data/test_data_amsr2/bg_data
    Checking for tgz files in /root/geoips/test_data/test_data_amsr2/bg_data//*/*.tgz...
    Checking for tgz files in /root/geoips/test_data/test_data_amsr2/bg_data//*/*/*.tgz...
    Checking for bz2 files in /root/geoips/test_data/test_data_amsr2/bg_data//*.bz2...
    Thu May 11 19:06:01 UTC 2023
    Checking for bz2 files in /root/geoips/test_data/test_data_amsr2/bg_data//*/*.bz2...
    Thu May 11 19:06:01 UTC 2023
        bunzip2 /root/geoips/test_data/test_data_amsr2/bg_data//*/*.bz2
    Checking for bz2 files in /root/geoips/test_data/test_data_amsr2/bg_data//*/*/*.bz2...
    Thu May 11 19:06:15 UTC 2023
    Checking for gz files in /root/geoips/test_data/test_data_amsr2/data/*.gz...
    Thu May 11 19:06:15 UTC 2023
        gunzip /root/geoips/test_data/test_data_amsr2/data/*.gz
    Checking for gz files in /root/geoips/test_data/test_data_amsr2/data/*/*.gz...
    Thu May 11 19:06:19 UTC 2023
    Checking for gz files in /root/geoips/test_data/test_data_amsr2/data/*/*/*.gz...
    Thu May 11 19:06:19 UTC 2023
    **Done cloning, updating and uncompressing test_data_amsr2.git

    WARNING: 'ls /root/geoips/test_data/test_data_amsr2/data/*' initially failed.
        Installed repo test_data_amsr2, please re-run test command.

    WARNING: 'ls /root/geoips/test_data/test_data_noaa_aws/data/*' failed.
        Installing repo test_data_abi_day.

    ** Setting up abi test data, from publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19/ to /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950/

    NOAA Geostationary Operational Environmental Satellites (GOES) 16 & 17 was accessed on
    Thu May 11 19:06:19 UTC 2023 from https://registry.opendata.aws/noaa-goes.

    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf lsf publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19/
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C01_G16_s20202621950205_e20202621959513_c20202621959567.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:       77.987 MiB / 77.987 MiB, 100%, 28.497 MiB/s, ETA 0s
    Transferred:            1 / 1, 100%
    Elapsed time:         2.9s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C02_G16_s20202621950205_e20202621959513_c20202621959546.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:      431.752 MiB / 431.752 MiB, 100%, 21.370 MiB/s, ETA 0s
    Transferred:            1 / 1, 100%
    Elapsed time:        20.8s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C03_G16_s20202621950205_e20202621959513_c20202621959570.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:       87.687 MiB / 87.687 MiB, 100%, 21.332 MiB/s, ETA 0s
    Transferred:            1 / 1, 100%
    Elapsed time:         4.1s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C04_G16_s20202621950205_e20202621959513_c20202621959534.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:       14.284 MiB / 14.284 MiB, 100%, 0 B/s, ETA -
    Transferred:            1 / 1, 100%
    Elapsed time:         1.3s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C05_G16_s20202621950205_e20202621959513_c20202621959562.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:       83.798 MiB / 83.798 MiB, 100%, 27.334 MiB/s, ETA 0s
    Transferred:            1 / 1, 100%
    Elapsed time:         3.4s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C06_G16_s20202621950205_e20202621959518_c20202621959556.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:       20.227 MiB / 20.227 MiB, 100%, 16.995 MiB/s, ETA 0s
    Transferred:            1 / 1, 100%
    Elapsed time:         1.5s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C07_G16_s20202621950205_e20202621959524_c20202621959577.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:       24.856 MiB / 24.856 MiB, 100%, 15.993 MiB/s, ETA 0s
    Transferred:            1 / 1, 100%
    Elapsed time:         1.7s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C08_G16_s20202621950205_e20202621959513_c20202621959574.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:       18.699 MiB / 18.699 MiB, 100%, 0 B/s, ETA -
    Transferred:            1 / 1, 100%
    Elapsed time:         1.3s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C09_G16_s20202621950205_e20202621959518_c20202621959588.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:       17.533 MiB / 17.533 MiB, 100%, 0 B/s, ETA -
    Transferred:            1 / 1, 100%
    Elapsed time:         1.3s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C10_G16_s20202621950205_e20202621959524_c20202621959578.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:       21.470 MiB / 21.470 MiB, 100%, 19.987 MiB/s, ETA 0s
    Transferred:            1 / 1, 100%
    Elapsed time:         1.4s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C11_G16_s20202621950205_e20202621959513_c20202621959583.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:       28.065 MiB / 28.065 MiB, 100%, 17.994 MiB/s, ETA 0s
    Transferred:            1 / 1, 100%
    Elapsed time:         1.6s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C12_G16_s20202621950205_e20202621959518_c20202621959574.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:       23.205 MiB / 23.205 MiB, 100%, 18.585 MiB/s, ETA 0s
    Transferred:            1 / 1, 100%
    Elapsed time:         1.5s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C13_G16_s20202621950205_e20202621959525_c20202622000005.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:       28.422 MiB / 28.422 MiB, 100%, 16.982 MiB/s, ETA 0s
    Transferred:            1 / 1, 100%
    Elapsed time:         1.8s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C14_G16_s20202621950205_e20202621959513_c20202622000009.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:       28.273 MiB / 28.273 MiB, 100%, 20.976 MiB/s, ETA 0s
    Transferred:            1 / 1, 100%
    Elapsed time:         1.5s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C15_G16_s20202621950205_e20202621959518_c20202621959594.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:       27.736 MiB / 27.736 MiB, 100%, 16.987 MiB/s, ETA 0s
    Transferred:            1 / 1, 100%
    Elapsed time:         1.7s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C16_G16_s20202621950205_e20202621959524_c20202622000001.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:       19.294 MiB / 19.294 MiB, 100%, 17.996 MiB/s, ETA 0s
    Transferred:            1 / 1, 100%
    Elapsed time:         1.4s
    ** Setting up abi test data, from publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19/ to /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950/

    NOAA Geostationary Operational Environmental Satellites (GOES) 16 & 17 was accessed on
    Thu May 11 19:07:10 UTC 2023 from https://registry.opendata.aws/noaa-goes.

    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf lsf publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19/
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C01_G16_s20202621950205_e20202621959513_c20202621959567.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:              0 B / 0 B, -, 0 B/s, ETA -
    Elapsed time:         0.3s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C02_G16_s20202621950205_e20202621959513_c20202621959546.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:              0 B / 0 B, -, 0 B/s, ETA -
    Elapsed time:         0.3s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C03_G16_s20202621950205_e20202621959513_c20202621959570.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:              0 B / 0 B, -, 0 B/s, ETA -
    Elapsed time:         0.4s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C04_G16_s20202621950205_e20202621959513_c20202621959534.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:              0 B / 0 B, -, 0 B/s, ETA -
    Elapsed time:         0.3s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C05_G16_s20202621950205_e20202621959513_c20202621959562.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:              0 B / 0 B, -, 0 B/s, ETA -
    Elapsed time:         0.4s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C06_G16_s20202621950205_e20202621959518_c20202621959556.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:              0 B / 0 B, -, 0 B/s, ETA -
    Elapsed time:         0.4s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C07_G16_s20202621950205_e20202621959524_c20202621959577.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:              0 B / 0 B, -, 0 B/s, ETA -
    Elapsed time:         0.3s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C08_G16_s20202621950205_e20202621959513_c20202621959574.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:              0 B / 0 B, -, 0 B/s, ETA -
    Elapsed time:         0.3s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C09_G16_s20202621950205_e20202621959518_c20202621959588.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:              0 B / 0 B, -, 0 B/s, ETA -
    Elapsed time:         0.3s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C10_G16_s20202621950205_e20202621959524_c20202621959578.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:              0 B / 0 B, -, 0 B/s, ETA -
    Elapsed time:         0.3s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C11_G16_s20202621950205_e20202621959513_c20202621959583.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:              0 B / 0 B, -, 0 B/s, ETA -
    Elapsed time:         0.3s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C12_G16_s20202621950205_e20202621959518_c20202621959574.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:              0 B / 0 B, -, 0 B/s, ETA -
    Elapsed time:         0.3s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C13_G16_s20202621950205_e20202621959525_c20202622000005.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:              0 B / 0 B, -, 0 B/s, ETA -
    Elapsed time:         0.3s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C14_G16_s20202621950205_e20202621959513_c20202622000009.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:              0 B / 0 B, -, 0 B/s, ETA -
    Elapsed time:         0.4s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C15_G16_s20202621950205_e20202621959518_c20202621959594.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:              0 B / 0 B, -, 0 B/s, ETA -
    Elapsed time:         0.3s
    rclone --config /root/geoips/geoips/setup/rclone_setup/rclone.conf copy -P publicAWS:noaa-goes16/ABI-L1b-RadF/2020/262/19//OR_ABI-L1b-RadF-M6C16_G16_s20202621950205_e20202621959524_c20202622000001.nc /root/geoips/test_data/test_data_noaa_aws/data/goes16/20200918/1950//
    Transferred:              0 B / 0 B, -, 0 B/s, ETA -
    Elapsed time:         0.3s

    $> ./tests/integration_tests/base_test.sh
    SUCCESS: 'git lfs install' appears to be installed successfully
        /root/micromamba/envs/geoips/bin/git

    SUCCESS: 'imagemagick' appears to be installed successfully
        /root/micromamba/envs/geoips/bin/compare

    SUCCESS: 'wget' appears to be installed successfully
        /usr/bin/wget

    SUCCESS: 'git' appears to be installed successfully
        /root/micromamba/envs/geoips/bin/git

    SUCCESS: 'python' appears to be installed successfully
        /root/micromamba/envs/geoips/bin/python

    SUCCESS: 'scipy/openblas' appear to be installed successfully

    SUCCESS: 'cartopy/libgeos' appear to be installed successfully

    SUCCESS: 'rclone' appears to be installed successfully
        /root/micromamba/envs/geoips/bin/rclone

    SUCCESS: repo 'test_data_amsr2' appears to be installed successfully
        drwxr-xr-x 6 root root 4096 May 11 19:05 /root/geoips/test_data/test_data_amsr2

    SUCCESS: repo 'test_data_abi_day' appears to be installed successfully
        drwxr-xr-x 3 root root 4096 May 11 19:06 /root/geoips/test_data/test_data_noaa_aws
    Thu May 11 19:10:19 UTC 2023 Running pre, log: /root/geoips/test_data/logs/20230511/20230511.191019_geoips_base/test_all_geoips_base.log

    Thu May 11 19:10:19 UTC 2023  Running abi.config_based_output.sh
    /root/geoips/geoips/tests/scripts/abi.config_based_output.sh
    /root/geoips/test_data/logs/20230511/20230511.191019_geoips_base/test_all_geoips_base.log_abi.config_based_output.sh.log
            Return: 0

    Thu May 11 19:12:54 UTC 2023  Running abi.static.Visible.imagery_annotated.sh
    /root/geoips/geoips/tests/scripts/abi.static.Visible.imagery_annotated.sh
    /root/geoips/test_data/logs/20230511/20230511.191019_geoips_base/test_all_geoips_base.log_abi.static.Visible.imagery_annotated.sh.log
            Return: 0

    Thu May 11 19:13:16 UTC 2023  Running test_interfaces
    test_interfaces
    /root/geoips/test_data/logs/20230511/20230511.191019_geoips_base/test_all_geoips_base.log_test_interfaces.log
            Return: 0


    Thu May 11 19:13:38 UTC 2023  Running post, final results in /root/geoips/test_data/logs/20230511/20230511.191019_geoips_base/test_all_geoips_base.log

    Package: geoips_base
    Total run time: 199 seconds
    Number data types run: 3
    Number data types failed: 0
