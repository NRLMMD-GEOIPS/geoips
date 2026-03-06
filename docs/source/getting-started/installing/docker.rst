.. _docker-builds:

Docker Builds
=============

GeoIPS ships a multi-stage Dockerfile that uses Ansible playbooks internally
to install the software.  Each stage corresponds to an installation tier and
can be targeted independently.

.. contents:: On this page
   :local:
   :depth: 2


Quick start
-----------

.. code-block:: bash

   # Build the full image (most common for development and CI)
   docker build --target geoips-full -t geoips:full .

   # Download test data to a host directory
   make testdata-full TESTDATA=/data/geoips-testdata

   # Run integration tests with test data mounted
   docker run --rm \
     -v /data/geoips-testdata:/geoips_testdata \
     geoips:full \
     pytest -vv -m "base and integration"


Build targets
-------------

The Dockerfile defines the following stages.  Each inherits from the one
above it, so ``geoips-site`` includes everything from ``geoips-full`` and
``geoips-base``.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Target
     - Description
   * - ``base-os``
     - System packages only (``git``, ``g++``, ``gfortran``, etc.).  Not
       intended for direct use.
   * - ``deps``
     - ``base-os`` plus all Python requirements from ``requirements.txt``,
       compiled from source with ``--no-binary :all:``.  This layer is cached
       by Docker and only rebuilds when ``requirements.txt`` changes.
   * - ``geoips-base``
     - Core GeoIPS installed (non-editable) and plugin registries created.
   * - ``geoips-full``
     - ``geoips-base`` plus cartopy shapefiles, settings repos, and
       ``doc``/``test`` pip extras.
   * - ``geoips-site``
     - ``geoips-full`` plus all open-source plugin packages (including
       the fortran chain) and ``lint``/``debug`` extras.
   * - ``production``
     - Minimal runtime image.  Copies only ``site-packages`` and console
       scripts from ``geoips-base``.  No source tree, no Ansible, no git,
       no compilers.

.. code-block:: bash

   docker build --target geoips-base -t geoips:base .
   docker build --target geoips-full -t geoips:full .
   docker build --target geoips-site -t geoips:site .
   docker build --target production  -t geoips:prod .


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
   * - ``GEOIPS_MODIFIED_BRANCH``
     - ``""``
     - After cloning each repo, attempt to check out this branch.
   * - ``GEOIPS_USE_PRIVATE_PLUGINS``
     - ``false``
     - Set to ``true`` at the ``geoips-site`` target to include private repos.
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
     --build-arg GEOIPS_USE_PRIVATE_PLUGINS=true \
     --build-arg GEOIPS_MODIFIED_BRANCH=feature/my-branch \
     .


Layer caching strategy
----------------------

The Dockerfile is structured to maximise Docker layer cache hits:

1. **``base-os``** — Changes only when the base image or system packages
   change (rare).

2. **``deps``** — Copies *only* ``environments/requirements.txt`` and
   installs all Python dependencies with ``--no-binary :all:``.  This is the
   slowest layer but it rebuilds only when ``requirements.txt`` changes.
   Day-to-day source edits skip this entirely.

3. **``geoips-base``** — Copies the full source tree and runs the Ansible
   install playbook.  Rebuilds on every source change but the heavy
   dependencies are already cached in ``deps``.

For the best cache performance, avoid editing ``requirements.txt`` unless
you are actually changing dependencies.


Building from source
--------------------

All Docker stages compile Python packages from source rather than using
pre-built wheels.  This is controlled by two mechanisms:

- The ``deps`` stage passes ``--no-binary :all:`` directly to ``pip install``
  when installing ``requirements.txt``.

- Each Ansible playbook invocation passes ``-e 'pip_extra_args=--no-binary
  :all:'`` so that GeoIPS itself, its extras, and any plugin packages are
  also compiled from source.

This ensures binaries are optimised for the container's architecture and
eliminates wheel bloat.  ``ansible-core`` is the sole exception — it keeps
its wheel because it is a build-time tool stripped from the production image.


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

   mkdir -p /data/geoips-testdata

   docker run --rm \
     -v /data/geoips-testdata:/geoips_testdata \
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

   make testdata-full TESTDATA=/data/geoips-testdata

The downloaded data persists on the host.  Subsequent runs are fast because
``geoips config install`` is idempotent.

Run tests with mounted data
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   docker run --rm \
     -v /data/geoips-testdata:/geoips_testdata \
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

The Makefile provides convenience wrappers:

.. code-block:: bash

   # Build images
   make build-base
   make build-full
   make build-site EXTRA_PLUGINS=my_plugin
   make build-production

   # Download test data (to host, via Docker)
   make testdata-base TESTDATA=/data/geoips-testdata
   make testdata-full TESTDATA=/data/geoips-testdata
   make testdata-site TESTDATA=/data/geoips-testdata

   # Run tests
   make test-base  TESTDATA=/data/geoips-testdata
   make test-full  TESTDATA=/data/geoips-testdata
   make test-unit


CI workflow
-----------

The GitHub Actions workflow (``.github/workflows/ci.yml``) automates the
full cycle:

1. **build** — Builds the Docker image at the configured tier.
2. **lint-and-unit** — Runs linting and unit tests (no test data required).
   Runs in parallel with step 3.
3. **test-data** — Downloads test datasets using the Ansible ``test_data.yml``
   playbook inside a Docker container with a host volume.  On self-hosted
   runners the data is cached between CI runs.
4. **integration** — Runs integration tests with the downloaded data mounted.
   Uses a matrix strategy to run ``base`` and ``full`` markers in parallel.
5. **push** *(optional)* — Pushes the image to a Docker registry if
   ``ENABLE_DOCKER_REGISTRY`` is set.

Configure the workflow using GitHub repository variables:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Variable
     - Description
   * - ``RUNNER``
     - Runner label (default: ``ubuntu-latest``).
   * - ``DOCKER_BUILD_TARGET``
     - Which Dockerfile stage to build (default: ``geoips-full``).
   * - ``TESTDATA_PATH``
     - Host path for test data (default: ``/data/geoips-testdata``).
   * - ``EXTRA_PLUGINS``
     - Comma-separated list of extra plugin repos.
   * - ``CI_LINT``
     - Set to ``false`` to skip linting.
   * - ``CI_INTEGRATION``
     - Set to ``false`` to skip integration tests.
   * - ``ENABLE_DOCKER_REGISTRY``
     - Set to ``true`` to enable image push.
   * - ``DOCKER_REGISTRY``
     - Registry URL for push.
   * - ``DOCKER_REGISTRY_USER``
     - Registry username.
