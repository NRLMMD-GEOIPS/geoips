.. _docker-builds:

Docker Builds
=============

GeoIPS ships a multi-stage Dockerfile that uses Ansible playbooks internally
to install the software.  Each stage adds one layer of the installation and
can be targeted independently.

.. contents:: On this page
   :local:
   :depth: 2


Quick start
-----------

The commands below build a Docker image with a ``full`` GeoIPS installation
(core plus cartopy shapefiles, settings repos, and ``doc``/``test`` extras),
download the required test datasets to a host directory, and run the
base integration tests with the data mounted into the container.

.. code-block:: bash

   # Build the full image (most common for development and CI)
   docker build --target geoips-full -t geoips:full .

   # Download test data to a host directory
   make testdata-full TESTDATA=/path/on/host/geoips-testdata

   # Run integration tests with test data mounted
   docker run --rm \
     -v /path/on/host/geoips-testdata:/geoips_testdata \
     geoips:full \
     pytest -vv -m "base and integration"


Build targets
-------------

The Dockerfile defines the stages below.  ``deps`` builds on ``base-os``;
``geoips-base``, ``geoips-full``, ``geoips-site`` and ``dev`` each build on
the one before; ``doclinttest`` and ``dev-quick`` branch off ``geoips-base``,
and ``production`` branches off ``base-os``.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Target
     - Description
   * - ``base-os``
     - ``python:3.11-slim-trixie`` with the system packages (``git``,
       ``wget``, ``libopenblas-dev``, ``g++``, ``make``, ``gfortran``,
       ``libeccodes-dev`` and ``gdal``) and ``uv``.  Not intended for direct
       use.
   * - ``deps``
     - ``base-os`` plus every pinned requirement from
       ``environments/requirements.txt``, ``ansible-core``, and the cartopy
       natural-earth shapefiles (cloned once to ``/packages/shapefiles_clone``
       and symlinked into ``/packages/shapefiles``).  This layer is cached by
       Docker and only rebuilds when ``requirements.txt`` or the Dockerfile
       changes.
   * - ``geoips-base``
     - ``deps`` plus the GeoIPS source tree installed non-editable and the
       Ansible ``base`` tier (system checks and plugin registries).
   * - ``doclinttest``
     - ``geoips-base`` plus the ``doc``, ``lint`` and ``test`` extras.  Used
       for documentation and lint CI; not a runtime image.
   * - ``geoips-full``
     - ``geoips-base`` plus the ``doc``/``test`` extras and the Ansible
       ``full`` tier (the settings repos ``.vscode``, ``.github`` and
       ``geoips_ci``).
   * - ``geoips-site``
     - ``geoips-full`` plus the ``site`` tier — all open-source plugin
       packages (including the ordered fortran chain) and the
       ``lint``/``debug`` extras.  Private plugin repos are included when
       ``GEOIPS_USE_PRIVATE_PLUGINS=true``.  Installed editable unless
       ``EDITABLE_PIP_INSTALL=false``.
   * - ``dev``
     - ``geoips-site`` converted to an editable install, plus developer tools
       (``openssh-server``, ``vim``, ``htop``, ``curl``, ``bash-completion``)
       and an sshd configuration.  This is the target used by the
       :ref:`dev container <dev-container>`.
   * - ``dev-quick``
     - ``geoips-base`` plus an editable install of the ``doc``, ``test``,
       ``lint`` and ``debug`` extras and the same developer tools.  No plugin
       packages and no settings repos, so it builds in a fraction of the time.
   * - ``production``
     - Minimal runtime image.  Copies only ``site-packages`` and the
       console-script stubs from ``geoips-base`` and removes the build tools.
       No source tree, no Ansible, no git, no compilers.

.. code-block:: bash

   docker build --target geoips-base -t geoips:base .
   docker build --target geoips-full -t geoips:full .
   docker build --target geoips-site -t geoips:site .
   docker build --target dev        -t geoips:dev .
   docker build --target dev-quick  -t geoips:dev-quick .
   docker build --target production -t geoips:prod .


Build arguments
---------------

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Argument
     - Default
     - Description
   * - ``EXTRA_PLUGINS``
     - ``""``
     - Comma-separated list of additional plugin repository names to clone
       and install at any tier.
   * - ``REPO_BRANCHES``
     - ``""``
     - ``"repo=ref repo=ref ..."``: clone these repos at a branch, tag or
       commit instead of their default branch (``geoips-full`` and
       ``geoips-site``), e.g. ``"recenter_tc=my-fix geocolor=v1.2.0"``.
       ``repo=owner:ref`` clones the ref from ``owner``'s fork of the repo.
       A ref that does not exist fails the build.
   * - ``DISABLED_REPOS``
     - ``""``
     - ``"repo repo ..."``: plugin repos to leave out of the install
       (``geoips-full`` and ``geoips-site``).
   * - ``PIP_OVERRIDES``
     - ``""``
     - pip requirements, one per line, installed last in ``geoips-site``
       so they replace the pinned versions.  For testing only.
   * - ``GEOIPS_USE_PRIVATE_PLUGINS``
     - ``false``
     - Set to ``true`` at the ``geoips-site`` target (inherited by ``dev``)
       to include the private plugin repos.  Needs the
       ``geoips_private_token`` secret (see below).
   * - ``EDITABLE_PIP_INSTALL``
     - ``true``
     - ``geoips-site``: ``true`` installs GeoIPS and the plugins editable,
       ``false`` installs them into ``site-packages``.  The ``dev`` stage
       re-runs the site tier editable regardless of this value;
       ``geoips-base`` and ``geoips-full`` always pass
       ``editable_pip_install=false``.
   * - ``USER``
     - ``geoips_user``
     - Username for the non-root user inside the container.
   * - ``USER_ID``
     - ``1000``
     - UID for the non-root user.
   * - ``GROUP_ID``
     - ``1000``
     - GID for the non-root user.

Example with build arguments:

.. code-block:: bash

   docker build --target geoips-site -t geoips:site \
     --build-arg EXTRA_PLUGINS=my_plugin,other_plugin \
     --build-arg REPO_BRANCHES="recenter_tc=feature/my-branch" \
     .

The private plugin repositories also need a GitHub token with read access to
them.  It is passed as a BuildKit secret and never stored in an image layer or
the image history:

.. code-block:: bash

   docker build --target geoips-site -t geoips:site-private \
     --build-arg GEOIPS_USE_PRIVATE_PLUGINS=true \
     --secret id=geoips_private_token,src=$HOME/.config/geoips/github-token .

Do not push such an image to a public registry: it contains the private
plugins' source.  See ``tests/ansible/scripts/github-token-env.sh``.


Layer caching strategy
----------------------

The Dockerfile is structured to maximise Docker layer cache hits:

1. **``base-os``** — Changes only when the base image or system packages
   change (rare).

2. **``deps``** — Copies *only* ``environments/requirements.txt`` and
   installs the pinned dependencies with ``uv pip install --system``, so it is
   the slowest layer but rebuilds only when ``requirements.txt`` or the
   Dockerfile changes.  Day-to-day source edits skip this entirely.

3. **``geoips-base``** — Copies the full source tree and runs the Ansible
   install playbook.  Rebuilds on every source change but the heavy
   dependencies are already cached in ``deps``.

For the best cache performance, avoid editing ``requirements.txt`` unless
you are actually changing dependencies.


Editable and non-editable installs
----------------------------------

Every stage installs Python packages with ``uv pip install --system
--no-cache`` into ``/usr/local``, so the interpreter is
``/usr/local/bin/python``.  Wheels are used when available; the pinned
versions come from ``environments/requirements.txt`` and the project's
``pyproject.toml``.  There is no ``--no-binary`` / ``pip_extra_args`` override
in the Dockerfile.

What differs between stages is whether GeoIPS and its plugins are installed
editable:

- ``geoips-base`` installs GeoIPS non-editable with ``uv pip install
  --system``, and runs the playbook with ``-e editable_pip_install=false``
  (the ``python_env`` role is skipped because uv already installed it).
  ``geoips-full`` installs the extras the same way.  This keeps the
  ``production`` image free of the source tree.
- ``geoips-site`` uses ``-e editable_pip_install=$EDITABLE_PIP_INSTALL``
  (``true`` by default).
- ``dev`` re-runs the ``site`` tier with ``-e editable_pip_install=true`` so
  that the workspace bind mount at ``/packages/geoips`` is the code that runs.
- ``dev-quick`` installs
  ``/packages/geoips[doc,test,lint,debug]`` editable directly.


Test data
---------

Test data is **never baked into Docker images**.  It is downloaded separately
and mounted at runtime.

Download test data using Ansible inside Docker
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The built image already has ``geoips`` and ``ansible-core`` installed, so
you can run the test data playbook directly inside a container with a host
volume:

.. code-block:: bash

   mkdir -p /path/on/host/geoips-testdata

   docker run --rm \
     -v /path/on/host/geoips-testdata:/geoips_testdata \
     -e ANSIBLE_CONFIG=/packages/geoips/tests/ansible/ansible.cfg \
     geoips:full \
     ansible-playbook \
       /packages/geoips/tests/ansible/playbooks/test_data.yml \
       -i /packages/geoips/tests/ansible/inventory/local.yml \
       --tags base,full \
       -e geoips_testdata_dir=/geoips_testdata \
       -v

Or use the Makefile wrapper:

.. code-block:: bash

   make testdata-full TESTDATA=/path/on/host/geoips-testdata

The downloaded data persists on the host.  Subsequent runs are fast because
``geoips config install`` is idempotent.

Run tests with mounted data
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   docker run --rm \
     -v /path/on/host/geoips-testdata:/geoips_testdata \
     -e GEOIPS_TESTDATA_DIR=/geoips_testdata \
     geoips:full \
     pytest -vv -m "base and integration"


Production image
----------------

The ``production`` target produces a minimal image suitable for deployment.
It copies only ``site-packages`` and console-script stubs from the builder
stage — no source tree, no Ansible, no test infrastructure, and no compilers.

.. code-block:: bash

   docker build --target production -t geoips:prod .
   docker run --rm geoips:prod --help

Build-time tools (``git``, ``make``, ``g++``, ``gfortran``, ``wget``) are
removed via ``apt-get remove`` to further reduce image size.


Make targets
------------

The ``Makefile`` at the root of the GeoIPS repository provides convenience wrappers:

.. code-block:: bash

   # Build images (tags default to geoips:<stage>-dev)
   make build-base
   make build-full
   make build-site EXTRA_PLUGINS=my_plugin
   make build-dev
   make build-dev-quick
   make build-production

   # Download test data (to host, via Docker)
   make testdata-base TESTDATA=/path/on/host/geoips-testdata
   make testdata-full TESTDATA=/path/on/host/geoips-testdata
   make testdata-site TESTDATA=/path/on/host/geoips-testdata

   # Run tests
   make test-base  TESTDATA=/path/on/host/geoips-testdata
   make test-full  TESTDATA=/path/on/host/geoips-testdata
   make test-unit

``TESTDATA`` defaults to ``$GEOIPS_TESTDATA_DIR`` and then to
``$HOME/.geoips/testdata``, the same directory the dev container mounts.
Set ``GEOIPS_USE_PRIVATE_PLUGINS=true`` to build ``geoips-site``/``dev`` with
the private plugin repos.


Dev container
-------------

The repository also ships a VS Code Dev Containers / ``devcontainer`` CLI
configuration in ``.devcontainer/``.  It builds the ``dev`` target and mounts
your checkout at ``/packages/geoips`` (through the editable install), the
host test data and output directories, and starts sshd on port 2222 with a
post-start command.
See :ref:`dev-container` for the host directories, the git worktree handling
and how to include the private plugins in the image.


CI workflow
-----------

Integration testing runs from ``.github/workflows/integ_test.yaml``.  On pull
requests (and on manual ``workflow_dispatch``) it calls the reusable workflow
``NRLMMD-GEOIPS/geoips_ci/.github/workflows/reusable-ci.yaml``, which builds
the image, downloads the test datasets and runs the tests.  The job requests
an editable install and forwards three secrets:

- ``token`` — ``GITHUB_TOKEN``, for cloning and status updates.
- ``docker_token`` — ``DOCKER_TOKEN``, for the image registry.
- ``private_repos_token`` — ``GEOIPS_PRIVATE_REPOS_TOKEN``, a read-only token
  for the private plugin repositories.  Without it the image contains the
  public plugins only.

``.github/workflows/build-stable-image.yaml`` builds and publishes the
``stable`` / ``latest`` images on releases and on pushes to the default
branch, also through a reusable ``geoips_ci`` workflow.

The devcontainer build args and secrets are described in
:ref:`dev-container`; ``make`` targets are the simplest way to reproduce a CI
build locally.
