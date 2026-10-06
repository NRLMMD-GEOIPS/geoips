.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _ci-infrastructure:

CI and Installation Infrastructure
==================================

GeoIPS uses `Ansible <https://docs.ansible.com/>`_ playbooks to manage installation of the
software, its plugins, and test datasets for CI purposes.  The same playbooks run on bare-metal developer
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
    ├── inventory/
    │   └── local.yml             # localhost, local connection, all variables live here
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

The ``Makefile`` provides convenience wrappers for every command shown below;
see `Make targets`_ for shortcuts you can use instead of typing Ansible commands
directly.


Prerequisites
-------------

Install ``ansible-core`` into the same Python environment used for GeoIPS:

.. code-block:: bash

   pip install ansible-core

CI runners pre-install ``ansible-core``; this step is only needed for local
development.  If you are running tests through the Docker-based CI (``make test-*``),
the container already includes it.

.. note::

   If you installed GeoIPS with ``pip install geoips[test]``, Ansible-core is
   already included and the standalone ``pip install ansible-core`` above can be
   skipped.

Set the standard GeoIPS environment variables before running any playbook.  The
``inventory/local.yml`` file reads these with ``lookup('env', ...)`` and falls back to
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
----------------------------

All commands below assume the repository root as the working directory.

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

Installing specific extra plugin packages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pass a comma-separated list of repository names:

.. code-block:: bash

   cd tests/ansible
   ansible-playbook playbooks/install.yml --tags base \
     -e extra_plugin_packages=my_plugin,other_plugin


Configuration variables
-----------------------

Override any variable with ``-e`` on the command line.  Defaults live in
``tests/ansible/inventory/local.yml`` and are resolved (in order) from environment variables,
then hardcoded defaults.  Copy the inventory file to create a custom setup
(e.g. ``inventory/my-setup.yml``) and run playbooks with ``-i inventory/my-setup.yml``.

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Variable
     - Default
     - Description
   * - ``editable_pip_install``
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
     - Set to ``true`` to include proprietary plugin repos (``pyrocb``,
       ``geoips_nucaps``, ``geoips_proxyvis``, ``geoips_tomorrowio``, ``geoips_wsfm``,
       ``geoips_xesmf``, ``ryglickicane``, ``geoips_debra``).
   * - ``extra_plugin_packages``
     - ``""``
     - Comma-separated list of additional plugin repository names to clone and install.
       Corresponds to the ``EXTRA_PLUGINS`` Docker build argument.
   * - ``repo_branches``
     - ``""``
     - ``"repo=ref repo=ref ..."``: clone these repos at a branch, tag or commit instead of
       their default branch.  Read from the ``REPO_BRANCHES`` environment variable.  See
       `Testing against other branches`_.
   * - ``disabled_repos``
     - ``""``
     - ``"repo repo ..."``: plugin repos to leave out of the install.  Read from the
       ``DISABLED_REPOS`` environment variable.  See `Disabling plugin repos`_.
   * - ``geoips_packages_dir``
     - ``/packages``
     - Root directory where repos are cloned.  Reads ``GEOIPS_PACKAGES_DIR`` env var.
   * - ``geoips_testdata_dir``
     - ``/geoips_testdata``
     - Root directory for test datasets.  Reads ``GEOIPS_TESTDATA_DIR`` env var.


Downloading test data
---------------------

Test data is managed by a **separate** playbook (``test_data.yml``) and is **never** baked
into Docker images.  It uses the same tier tags as the install playbook.

The ``test_data`` role wraps ``geoips config install``, which is idempotent — datasets
already present on disk are skipped.

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
---------------------

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

   Controlled by ``editable_pip_install`` and ``pip_extra_args``.

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
      → ``synth_green`` → ``geocolor`` → ``lunarref`` → ``true_color``
   3. **Private plugins** (when enabled): ``pyrocb``, ``geoips_nucaps``,
      ``geoips_proxyvis``, ``geoips_tomorrowio``, ``geoips_wsfm``, ``ryglickicane``
      (``geoips_xesmf`` is disabled for now: xesmf needs the ESMF library,
      which the image does not have)
   4. **Private fortran repos** (when enabled, order critical): ``geoips_debra``
   5. **Extra plugins**: any repos passed via ``extra_plugin_packages``

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


Make targets
^^^^^^^^^^^^

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
   make testdata-full TESTDATA=/path/on/host/geoips-testdata


Docker integration
------------------

The Dockerfile uses a multi-stage build that maps directly to the Ansible tiers:

.. code-block:: text

   deps       – pip install -r requirements.txt (cached layer)
   geoips-base – ansible-playbook ... --tags base
   geoips-full – ansible-playbook ... --tags base,full
   geoips-site – ansible-playbook ... --tags base,full,site
   production  – copy site-packages only, no source, no ansible, no git

**Why ``editable_pip_install=false`` in Docker?**  The editable install mode makes the source
directory itself the package.  In a container built for deployment this is undesirable —
the source tree may not be present at runtime.  Building with ``editable_pip_install=false``
installs the package into ``site-packages`` like a normal wheel, and the ``production``
stage then copies only that directory, producing a minimal image.

The ``dev`` and ``dev-quick`` Docker targets use ``editable_pip_install=true`` to enable
live source editing through the workspace bind-mount.

**Why ``--no-binary :all:``?**  Pre-built wheels are compiled for a generic architecture.
Compiling from source inside the container produces binaries optimized for the target CPU
and avoids wheel-cache bloat.  The ``deps`` stage also applies this flag, and because
``requirements.txt`` changes infrequently, Docker caches that layer across most rebuilds.

**Test data volume pattern:**

.. code-block:: bash

   # Download data to the host via the ansible playbook inside the container
   make testdata-full TESTDATA=/path/on/host/geoips-testdata

   # Run tests with that data mounted at the expected path
   docker run --rm -v /path/on/host/geoips-testdata:/geoips_testdata geoips:full \
     pytest -m "base and integration"

Test data is always a runtime mount, never a build-time layer.


Testing against other branches
------------------------------

Repos are cloned on their default branch.  To test a change that needs changes in other
repos or other package versions, add an entry for its branch to
``.github/ci-dependencies.yaml``:

.. code-block:: yaml

   my-feature-branch:
     python:   # pip requirements, installed last in the image so they win
       - "pluginify @ git+https://github.com/NRLMMD-GEOIPS/pluginify@my-fix"
       - "xarray==2025.6.1"
     repos:    # repos the image clones: repo -> branch, tag or commit
       recenter_tc: my-fix

geoips_ci passes these to the ``geoips-site`` build as ``PIP_OVERRIDES`` and
``REPO_BRANCHES``.  The playbook checks ``repo_branches`` before installing anything: an
unknown repo, or a private repo when the ``site`` tasks run without
``geoips_use_private_plugins``, fails the run, and
so does a ref that does not exist (there is no fallback to the default branch).  The image
records what the overrides installed in ``.ci_pip_overrides`` and ``.ci_repo_branches`` in
``$GEOIPS_PACKAGES_DIR``, which CI shows in the job summary.

Only the entry of the branch under test applies, so the file can be merged without
affecting ``main`` or other branches.  CI never pushes images built with overrides.
Plugin repos test in the published
GeoIPS image, so only ``python`` overrides apply there, for example
``geoips @ git+https://github.com/NRLMMD-GEOIPS/geoips@my-branch``.

Disabling plugin repos
----------------------

To leave plugin repos out of the CI image, for example while their install is broken,
list them in ``.github/ci-disabled-repos.yaml`` with the reason:

.. code-block:: yaml

   synth_green: "install fails, see NRLMMD-GEOIPS/synth_green#12"

Unlike ``.github/ci-dependencies.yaml``, this applies to every branch.  geoips_ci passes
the names to the image build as ``DISABLED_REPOS`` and lists them in the job summary.  The
playbook removes them from ``plugin_repos``, ``fortran_repos_ordered``,
``private_plugin_repos`` and ``private_fortran_repos`` (keeping the order), so they are
not cloned, installed or tested.  A name that is not in those lists, or that is also in
``repo_branches``, fails the run.  Repos that need a disabled repo still install, but
the parts that use it fail: geocolor's GeoColor products need ``synth_green``, for
example.


Idempotency
-----------

The playbooks are designed to be re-run safely at any point:

- ``ansible.builtin.git`` fails rather than overwrite uncommitted changes in an existing
  clone.
- ``pip install`` with ``state: present`` is a no-op when the package is already installed
  at the correct version.
- The ``test_data`` role uses ``creates: "{% raw %}{{ geoips_testdata_dir }}/{{ item }}{% endraw %}"`` so
  Ansible skips the ``geoips config install`` call entirely when the dataset directory
  already exists.
- ``geoips config create-registries`` is idempotent by design.

If a run fails partway through, fix the underlying issue and re-run the same command.
Completed tasks will execute as fast no-ops.  Multiple runs will not hurt anything.


Adding new repositories
-----------------------

Repositories and which install group they belong to are managed by
``tests/ansible/inventory/local.yml``.  To add a new repo or move a repo to a
different install group, edit ``tests/ansible/inventory/local.yml`` as follows:

**Standard plugin repos** (no ordering constraint):
   Add the repo name to ``plugin_repos`` in ``tests/ansible/inventory/local.yml``.

**Fortran plugin repos** (ordering constraint applies):
   Add the repo name to ``fortran_repos_ordered`` in ``inventory/local.yml`` in the
   correct position in the dependency chain.  The comment in that file documents the
   required order.

**Private repos**:
   Add to ``private_plugin_repos`` or ``private_fortran_repos`` (for the fortran chain)
   in ``inventory/local.yml``.

**Test datasets**:
   Add the dataset name to the appropriate tier list in
   ``tests/ansible/roles/test_data/defaults/main.yml``.  The name must be recognized by
   ``geoips config install``.


Troubleshooting
---------------

Increase verbosity
^^^^^^^^^^^^^^^^^^

Add ``-vvv`` to any ``ansible-playbook`` command for detailed task output:

.. code-block:: bash

   ansible-playbook playbooks/install.yml --tags base -vvv

Dry run
^^^^^^^

Use ``--check`` to see what Ansible *would* do without making any changes:

.. code-block:: bash

   ansible-playbook playbooks/install.yml --tags base --check

Re-running after a failure
^^^^^^^^^^^^^^^^^^^^^^^^^^

Ansible is idempotent.  Fix the underlying issue and re-run the same command.  Completed
tasks will be fast no-ops.
