.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _ci-infrastructure:

CI and Installation Infrastructure
===================================

GeoIPS uses `Ansible <https://docs.ansible.com/>`_ playbooks to manage installation of the
software, its plugins, and test datasets.  The same playbooks run on bare-metal developer
machines and inside Docker containers, replacing the legacy hand-written shell scripts
(``base_install.sh``, ``full_install.sh``, ``site_install.sh``,
``check_system_requirements.sh``).

Ansible is a **contributor and CI tool** — end users install GeoIPS via pip or conda, not
through these playbooks.

.. contents:: On this page
   :local:
   :depth: 2


Overview
--------

The playbooks live in ``tests/ansible/`` alongside a standard role layout::

    tests/ansible/
    ├── ansible.cfg               # inventory path, roles path, no host-key checking
    ├── group_vars/
    │   └── all.yml               # all variables with env-var fallbacks
    ├── inventory/
    │   └── local.yml             # localhost, local connection
    ├── playbooks/
    │   ├── install.yml           # software installation
    │   └── test_data.yml         # test dataset downloads
    └── roles/
        ├── system_deps/
        ├── python_env/
        ├── cartopy_shapefiles/
        ├── settings_repos/
        ├── source_repos/
        ├── registries/
        └── test_data/

Only ``ansible.builtin`` modules are used — no external Ansible collections are required.


Prerequisites
-------------

Install ``ansible-core`` into the same Python environment used for GeoIPS:

.. code-block:: bash

   pip install ansible-core

Set the standard GeoIPS environment variables before running any playbook.  The
``group_vars/all.yml`` file reads these with ``lookup('env', ...)`` and falls back to
reasonable defaults:

.. code-block:: bash

   export GEOIPS_PACKAGES_DIR=/path/to/packages
   export GEOIPS_OUTDIRS=/path/to/output
   export GEOIPS_TESTDATA_DIR=/path/to/testdata
   export GEOIPS_REPO_URL=https://github.com/NRLMMD-GEOIPS


Tier model
----------

GeoIPS installation is organized into three additive tiers controlled by Ansible tags.
Always include all lower tiers when running a higher one.

.. list-table::
   :header-rows: 1
   :widths: 10 90

   * - Tag
     - What it installs
   * - ``base``
     - Core GeoIPS package and plugin registries.  Sufficient for unit tests and
       basic import checks.
   * - ``full``
     - Everything in ``base``, plus cartopy natural-earth shapefiles, settings repos
       (``.vscode``, ``.github``, ``geoips_ci``), and ``doc``/``test`` pip extras.
       Required for integration tests that produce output imagery.
   * - ``site``
     - Everything in ``full``, plus all open-source plugin packages (standard repos and the
       ordered fortran chain), ``lint``/``debug`` pip extras, and optionally private repos.

The three-tier design maps directly to Docker image targets (see `Docker integration`_).
Tags are the single mechanism that controls depth — there are no separate playbooks for
each tier.


Running the install playbook
-----------------------------

All commands below assume the repository root as the working directory.

Base install (core GeoIPS only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   cd tests/ansible
   ansible-playbook playbooks/install.yml --tags base

Full install (base + shapefiles + test extras)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   cd tests/ansible
   ansible-playbook playbooks/install.yml --tags base,full

Site install (full + all plugin packages)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   cd tests/ansible
   ansible-playbook playbooks/install.yml --tags base,full,site

Site install with private repos
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   cd tests/ansible
   ansible-playbook playbooks/install.yml --tags base,full,site \
     -e geoips_use_private_plugins=true

Installing specific extra plugins
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pass a comma-separated list of repository names:

.. code-block:: bash

   cd tests/ansible
   ansible-playbook playbooks/install.yml --tags base \
     -e extra_plugins=my_plugin,other_plugin


Configuration variables
------------------------

Override any variable with ``-e`` on the command line.  Defaults live in
``tests/ansible/group_vars/all.yml`` and are resolved (in order) from environment variables,
then hardcoded defaults.

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Variable
     - Default
     - Description
   * - ``pip_editable``
     - ``true``
     - ``true`` uses ``pip install -e`` (editable — the source tree *is* the package).
       ``false`` builds from source into ``site-packages``, which produces a smaller Docker
       image.
   * - ``pip_extra_args``
     - ``""``
     - Additional arguments forwarded to every ``pip install`` call.  Docker builds use
       ``--no-binary :all:`` to compile all dependencies from source inside the container.
   * - ``geoips_use_private_plugins``
     - ``false``
     - Set to ``true`` to include proprietary plugin repos (``ryglickicane``, ``tc_mint``,
       ``lunarref``, ``true_color``).
   * - ``extra_plugins``
     - ``""``
     - Comma-separated list of additional plugin repository names to clone and install.
       Corresponds to the ``EXTRA_PLUGINS`` Docker build argument.
   * - ``geoips_modified_branch``
     - ``""``
     - After cloning each repo, attempt to check out this branch.  Falls back silently to
       the default branch if it does not exist.
   * - ``geoips_packages_dir``
     - ``/packages``
     - Root directory where repos are cloned.  Reads ``GEOIPS_PACKAGES_DIR`` env var.
   * - ``geoips_testdata_dir``
     - ``/geoips_testdata``
     - Root directory for test datasets.  Reads ``GEOIPS_TESTDATA_DIR`` env var.


Downloading test data
----------------------

Test data is managed by a **separate** playbook (``test_data.yml``) and is **never** baked
into Docker images.  It uses the same tier tags as the install playbook.

The ``test_data`` role wraps ``geoips config install``, which is idempotent — datasets
already present on disk are skipped.

Base datasets only
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   cd tests/ansible
   ansible-playbook playbooks/test_data.yml --tags base

Base + full datasets
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   cd tests/ansible
   ansible-playbook playbooks/test_data.yml --tags base,full

All datasets (including site + private)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   cd tests/ansible
   ansible-playbook playbooks/test_data.yml --tags base,full,site \
     -e geoips_use_private_plugins=true

Override the download location
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   cd tests/ansible
   ansible-playbook playbooks/test_data.yml --tags base \
     -e geoips_testdata_dir=/my/custom/path

**Why the separation?**  Test data is mounted into Docker containers at runtime via a host
volume — it is never built into an image.  Keeping the download in its own playbook enforces
this boundary and allows CI to cache the test-data volume between runs independently of image
rebuilds.

The datasets installed at each tier are defined in
``tests/ansible/roles/test_data/defaults/main.yml``:

- **base**: ``test_data_amsr2``
- **full**: ``test_data_amsub``, ``test_data_arctic_weather_satellite``, ``test_data_atms``,
  ``test_data_cygnss``, ``test_data_fci``, ``test_data_gfs``, ``test_data_gpm``,
  ``test_data_modis``, ``test_data_multi_scan_times``, ``test_data_saphir``,
  ``test_data_sar``, ``test_data_scat``, ``test_data_seviri``, ``test_data_smap``,
  ``test_data_smos``, ``test_data_tpw``, ``test_data_viirs``
- **site**: ``template_test_data``, ``test_data_clavrx``, ``test_data_fusion``,
  ``test_data_geocolor``
- **private** (``geoips_use_private_plugins=true``): ``test_data_mint``


Role responsibilities
----------------------

The roles live in ``tests/ansible/roles/`` and each handles one concern.

``system_deps``
   Verifies that required system commands (``git``, ``python3``, ``gcc``, ``gfortran``,
   ``g++``) are available.  Does **not** install them — the host OS or Docker base image
   is expected to provide them.  This role is a fast-fail guard so dependency errors
   surface immediately rather than mid-install.

``python_env``
   Installs GeoIPS and its pip extras at the tier-appropriate level:

   - ``base``: ``requirements.txt`` + ``pip install geoips``
   - ``full``: adds ``geoips[doc,test]``
   - ``site``: adds ``geoips[lint,debug]``

   Controlled by ``pip_editable`` and ``pip_extra_args``.

``cartopy_shapefiles``
   Clones the `natural-earth-vector <https://github.com/nvkelso/natural-earth-vector>`_
   repository (depth 1) and symlinks the shapefiles into the directory structure that
   cartopy expects.  Cultural and physical shapefiles are each symlinked in two passes —
   subdirectory contents first, then top-level files — replicating the logic of the old
   ``check_system_requirements.sh``.  Only runs at ``full`` and ``site`` tiers.

``settings_repos``
   Clones non-plugin reference repositories (``.vscode``, ``.github``, ``geoips_ci``) into
   ``$GEOIPS_PACKAGES_DIR``.  These repos provide IDE configuration, GitHub workflows, and
   CI scripts.  Only runs at ``full`` and ``site`` tiers.

``source_repos``
   Clones and ``pip install``\s plugin packages.  Handles four groups in order:

   1. **Standard plugins** (alphabetical): ``data_fusion``, ``geoips_clavrx``,
      ``geoips_plugin_example``, ``recenter_tc``, ``template_basic_plugin``
   2. **Fortran chain** (order critical): ``fortran_utils`` → ``rayleigh`` → ``ancildat``
      → ``synth_green`` → ``geocolor``
   3. **Private plugins** (when enabled): ``ryglickicane``, ``tc_mint``
   4. **Private fortran repos** (when enabled, order critical): ``lunarref``, ``true_color``
   5. **Extra plugins**: any repos passed via ``extra_plugins``

   The fortran ordering constraint exists because each package depends on compiled
   artifacts produced by the previous one.  Extra plugins are available at all tiers
   (``base``, ``full``, ``site``) to support CI matrix builds of individual plugins.

``registries``
   Runs ``geoips config create-registries`` as the final install step.  This command scans
   all installed GeoIPS plugin packages and writes the plugin registry files that GeoIPS
   reads at startup.  The task uses ``changed_when: false`` because the command is
   idempotent and does not report changes in its exit code.

``test_data``
   Downloads test datasets via ``geoips config install``.  Used exclusively by
   ``test_data.yml`` — it is not part of the install playbook.


Docker integration
-------------------

The Dockerfile uses a multi-stage build that maps directly to the Ansible tiers:

.. code-block:: text

   deps       – pip install -r requirements.txt (cached layer)
   geoips-base – ansible-playbook ... --tags base
   geoips-full – ansible-playbook ... --tags base,full
   geoips-site – ansible-playbook ... --tags base,full,site
   production  – copy site-packages only, no source, no ansible, no git

**Why ``pip_editable=false`` in Docker?**  The editable install mode makes the source
directory itself the package.  In a container built for deployment this is undesirable —
the source tree may not be present at runtime.  Building with ``pip_editable=false``
installs the package into ``site-packages`` like a normal wheel, and the ``production``
stage then copies only that directory, producing a minimal image.

**Why ``--no-binary :all:``?**  Pre-built wheels are compiled for a generic architecture.
Compiling from source inside the container produces binaries optimized for the target CPU
and avoids wheel-cache bloat.  The ``deps`` stage also applies this flag, and because
``requirements.txt`` changes infrequently, Docker caches that layer across most rebuilds.

**Test data volume pattern:**

.. code-block:: bash

   # Download data to the host via the ansible playbook inside the container
   make testdata-full TESTDATA=/data/geoips-testdata

   # Run tests with that data mounted at the expected path
   docker run --rm -v /data/geoips-testdata:/geoips_testdata geoips:full \
     pytest -m "base and integration"

Test data is always a runtime mount, never a build-time layer.


Branch fallback strategy
-------------------------

Every repo clone — in both ``settings_repos`` and ``source_repos`` — follows a two-step
pattern:

1. Attempt to clone (or checkout) the branch named by ``geoips_modified_branch``.  If that
   variable is empty, this step is skipped entirely.
2. If the branch clone failed (branch does not exist in the remote), fall back to the
   remote's default branch.

This lets CI pipelines pass a single branch name across all repos without needing to know
which repos actually carry that branch.  Repos that do not have the branch simply land on
their default branch without error.

The ``source_repos`` role implements this per-repo in
``roles/source_repos/tasks/clone_and_install.yml``.  The ``settings_repos`` role uses a
batch approach: clone all repos in one loop with ``failed_when: false``, then re-clone only
the ones that failed.


Idempotency
-----------

The playbooks are designed to be re-run safely at any point:

- ``ansible.builtin.git`` uses ``update: false`` on the fallback clone so it does not
  overwrite uncommitted changes.
- ``pip install`` with ``state: present`` is a no-op when the package is already installed
  at the correct version.
- The ``test_data`` role uses ``creates: "{{ geoips_testdata_dir }}/{{ item }}"`` so
  Ansible skips the ``geoips config install`` call entirely when the dataset directory
  already exists.
- ``geoips config create-registries`` is idempotent by design.

If a run fails partway through, fix the underlying issue and re-run the same command.
Completed tasks will execute as fast no-ops.


Adding new repositories
------------------------

**Standard plugin repos** (no ordering constraint):
   Add the repo name to ``plugin_repos`` in ``tests/ansible/group_vars/all.yml``.

**Fortran plugin repos** (ordering constraint applies):
   Add the repo name to ``fortran_repos_ordered`` in ``group_vars/all.yml`` in the
   correct position in the dependency chain.  The comment in that file documents the
   required order.

**Private repos**:
   Add to ``private_plugin_repos`` or ``private_fortran_repos`` (for the fortran chain)
   in ``group_vars/all.yml``.

**Test datasets**:
   Add the dataset name to the appropriate tier list in
   ``tests/ansible/roles/test_data/defaults/main.yml``.  The name must be recognized by
   ``geoips config install``.


Troubleshooting
----------------

Increase verbosity
^^^^^^^^^^^^^^^^^^^

Add ``-vvv`` to any ``ansible-playbook`` command for detailed task output:

.. code-block:: bash

   ansible-playbook playbooks/install.yml --tags base -vvv

Dry run
^^^^^^^^

Use ``--check`` to see what Ansible *would* do without making any changes:

.. code-block:: bash

   ansible-playbook playbooks/install.yml --tags base --check

Re-running after a failure
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ansible is idempotent.  Fix the underlying issue and re-run the same command.  Completed
tasks will be fast no-ops.

Make targets
^^^^^^^^^^^^^

The Makefile provides convenience wrappers:

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
