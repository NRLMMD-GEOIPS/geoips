.. _ansible-installation:

Ansible-Based Installation
==========================

GeoIPS uses `Ansible <https://docs.ansible.com/>`_ playbooks to manage
installation of the software, its plugins, and test datasets.  The same
playbooks work on bare-metal developer machines and inside Docker containers.

.. contents:: On this page
   :local:
   :depth: 2


Prerequisites
-------------

Install ``ansible-core`` into the same Python environment you will use for
GeoIPS:

.. code-block:: bash

   pip install ansible-core

No additional Ansible collections are required — only ``ansible.builtin``
modules are used.

You will also need the standard GeoIPS environment variables set:

.. code-block:: bash

   export GEOIPS_PACKAGES_DIR=/path/to/packages
   export GEOIPS_OUTDIRS=/path/to/output
   export GEOIPS_TESTDATA_DIR=/path/to/testdata
   export GEOIPS_REPO_URL=https://github.com/NRLMMD-GEOIPS


Installation tiers
------------------

GeoIPS installation is organized into three tiers controlled by Ansible tags.
Tags are additive — always include all lower tiers when running a higher one.

.. list-table::
   :header-rows: 1
   :widths: 10 90

   * - Tag
     - What it installs
   * - ``base``
     - Core GeoIPS package (``pip install``) and plugin registries.
   * - ``full``
     - Everything in base, plus cartopy shapefiles, settings repos
       (``.vscode``, ``.github``, ``geoips_ci``), and doc/test pip extras.
   * - ``site``
     - Everything in full, plus all open-source plugin packages (including the
       ordered fortran chain), lint/debug extras, and optionally private repos.


Running the install playbook
----------------------------

All commands below assume you are in the GeoIPS repository root.

Base install (core GeoIPS only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   cd tests/ansible
   ansible-playbook playbooks/install.yml --tags base

Full install (base + shapefiles + test extras)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   cd tests/ansible
   ansible-playbook playbooks/install.yml --tags base,full

Site install (full + all plugin packages)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   cd tests/ansible
   ansible-playbook playbooks/install.yml --tags base,full,site

Site install with private repos
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   cd tests/ansible
   ansible-playbook playbooks/install.yml --tags base,full,site \
     -e geoips_use_private_plugins=true

Installing specific extra plugins
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pass a comma-separated list of repository names:

.. code-block:: bash

   cd tests/ansible
   ansible-playbook playbooks/install.yml --tags base \
     -e extra_plugins=my_plugin,other_plugin


Configuration variables
-----------------------

Override any of these with ``-e`` on the command line.  Defaults are defined
in ``tests/ansible/group_vars/all.yml``.

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Variable
     - Default
     - Description
   * - ``pip_editable``
     - ``true``
     - ``true`` uses ``pip install -e`` (editable — the source tree *is* the
       package).  ``false`` builds from source into ``site-packages``, which
       produces a smaller Docker image.
   * - ``pip_extra_args``
     - ``""``
     - Additional arguments forwarded to every ``pip install`` call.  Docker
       builds use ``--no-binary :all:`` to compile everything from source.
   * - ``geoips_use_private_plugins``
     - ``false``
     - Set to ``true`` to include proprietary plugin repos such as
       ``ryglickicane`` and ``tc_mint``.
   * - ``extra_plugins``
     - ``""``
     - Comma-separated list of additional plugin repository names to clone and
       install.
   * - ``geoips_modified_branch``
     - ``""``
     - After cloning each repo, attempt to check out this branch.  Falls back
       to the default branch if it does not exist.


Downloading test data
---------------------

Test data is managed by a **separate** playbook (``test_data.yml``) and is
never baked into Docker images.  The ``test_data`` role wraps
``geoips config install``, which is idempotent — datasets already present on
disk are skipped.

Base datasets only
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   cd tests/ansible
   ansible-playbook playbooks/test_data.yml --tags base

Base + full datasets
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   cd tests/ansible
   ansible-playbook playbooks/test_data.yml --tags base,full

All datasets (including site + private)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   cd tests/ansible
   ansible-playbook playbooks/test_data.yml --tags base,full,site \
     -e geoips_use_private_plugins=true

Override the download location
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   cd tests/ansible
   ansible-playbook playbooks/test_data.yml --tags base \
     -e geoips_testdata_dir=/my/custom/path

The test data playbook uses the same tier tags as the install playbook so
the datasets match the software that was installed.


Ansible role reference
----------------------

The roles live in ``tests/ansible/roles/`` and each handles one concern:

``system_deps``
   Verifies that required system commands (``git``, ``python3``, ``gcc``,
   ``gfortran``, ``g++``) are available.  Does not install them — the host
   or Docker base image is expected to provide them.

``python_env``
   Installs GeoIPS and its pip extras (``doc``, ``test``, ``lint``, ``debug``)
   at the tier-appropriate level.

``cartopy_shapefiles``
   Clones the `natural-earth-vector <https://github.com/nvkelso/natural-earth-vector>`_
   repository and symlinks the shapefiles into the directory structure that
   cartopy expects.

``settings_repos``
   Clones non-plugin reference repositories (``.vscode``, ``.github``,
   ``geoips_ci``) into ``$GEOIPS_PACKAGES_DIR``.

``source_repos``
   Clones and ``pip install``\ s plugin packages.  Handles the fortran
   dependency chain (``fortran_utils`` → ``rayleigh`` → ``ancildat`` →
   ``synth_green`` → ``geocolor``) in the correct order.

``test_data``
   Downloads test datasets via ``geoips config install``.  Used by
   ``test_data.yml`` only — not part of the install playbook.

``registries``
   Runs ``geoips config create-registries`` as the final step of installation.


Using Make targets
------------------

The Makefile provides convenience wrappers for common operations:

.. code-block:: bash

   # Bare-metal install
   make ansible-base
   make ansible-full
   make ansible-site

   # Bare-metal test data download
   make ansible-testdata-base
   make ansible-testdata-full
   make ansible-testdata-site

   # Docker test data download (downloads to host via mounted volume)
   make testdata-full TESTDATA=/data/geoips-testdata

See :ref:`docker-builds` for Docker-specific Make targets.


Troubleshooting
---------------

Increase verbosity
^^^^^^^^^^^^^^^^^^

Add ``-vvv`` to any ``ansible-playbook`` command for detailed output:

.. code-block:: bash

   ansible-playbook playbooks/install.yml --tags base -vvv

Dry run
^^^^^^^

Use ``--check`` to see what ansible *would* do without making changes:

.. code-block:: bash

   ansible-playbook playbooks/install.yml --tags base --check

Re-running after a failure
^^^^^^^^^^^^^^^^^^^^^^^^^^

Ansible is idempotent.  If a run fails partway through, fix the underlying
issue and re-run the same command.  Completed tasks will be fast no-ops.
