(developer-installation)=

# Developer Installation

This guide is for developers who need the full GeoIPS development environment
with source code access, testing capabilities, and all plugins.

Following this source-based installation guide may help users who are
having difficulty with the pip installation due to dependency, architecture,
or OS issues.

**For the fully supported user installation with all dependencies managed
automatically, use the** {ref}`GeoIPS Installation Guide<installation>`.

## Prerequisites

Operating System:

- Linux (RedHat and Debian flavors officially supported)
- MacOS (Not officially supported)
- Windows with WSL2 (Not officially supported)

Python version 3.11 or higher. We recommend using [Mamba][mamba], [Miniconda][miniconda], or
[Anaconda][anaconda] to manage your python environment, but any Python 3.11+
installation should work. Please see the {ref}`system requirements
<system-requirements>` for more information.

Required system dependencies:

* git >= 2.19.1
* libopenblas-dev
* make
* g++ and gcc
* gfortran
* wget

## Environment Variables

Set these environment variables before installation:

```{code-block} bash

    export GEOIPS_REPO_URL=https://github.com/NRLMMD-GEOIPS
    export GEOIPS_PACKAGES_DIR=<installation_location>
    export GEOIPS_TESTDATA_DIR=<desired_test_data_location>
    export GEOIPS_OUTDIRS=<desired_output_file_location>
```

:::{tip}
These environment variables can be persisted either by adding them to your
shell environment (e.g. `.bashrc`) or by adding them to your conda
environment using `conda env config vars set
GEOIPS_OUTDIRS=$HOME/geoips_output`.
:::

## Installation Steps

```{code-block} bash

    # Clone the repository
    git clone $GEOIPS_REPO_URL/geoips.git $GEOIPS_PACKAGES_DIR/geoips

    # Install in editable mode
    pip install -e "$GEOIPS_PACKAGES_DIR/geoips[doc,lint,test,debug]"

    # Download the base test data and create the plugin registries
    "$GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/base_install.sh"

    # Run the base integration tests
    pytest -vv -m "base and integration"
```

## Plugin Installation Levels

The installation scripts in `tests/integration_tests/` mirror the Ansible tiers
used for the Docker images:

* **Base**: system checks, the core plugin registries and the AMSR2 test data
  (`base_install.sh`).
* **Full**: base plus cartopy shapefiles, ancillary data, the settings repos
  (`.vscode`, `.github`, `geoips_ci`) and the datasets the full tests need
  (`full_install.sh`).
* **Site**: full plus every open-source plugin package, the fortran chain and
  their test data (`site_install.sh`). Export
  `GEOIPS_USE_PRIVATE_PLUGINS=true` to include the private repositories.

# Docker Plugin Development Environment

For containerized plugin development, use the `dev` or `dev-quick` Docker
targets:

```{code-block} bash

    # Full plugin environment, editable (inherits geoips-site)
    docker build --target dev -t geoips:dev .
    # or: make build-dev

    # Core GeoIPS only: fast build, no plugin packages or settings repos
    docker build --target dev-quick -t geoips:dev-quick .
    # or: make build-dev-quick
```

Export `GEOIPS_USE_PRIVATE_PLUGINS=true` to include the private plugin
repositories; the GitHub token is passed as the `geoips_private_token` build
secret (see {ref}`docker-builds`). Available stages:

* **base-os**: system packages and `uv`
* **deps**: pinned Python requirements, `ansible-core`, cartopy shapefiles
* **geoips-base**: core GeoIPS, non-editable, plus plugin registries
* **doclinttest**: core plus the `doc`/`lint`/`test` extras (documentation and
  lint CI)
* **geoips-full**: `geoips-base` plus the settings repos and `doc`/`test`
  extras
* **geoips-site**: `geoips-full` plus all open-source plugin packages and the
  `lint`/`debug` extras
* **dev**: `geoips-site` converted to an editable install, plus developer
  tools and an sshd configuration
* **dev-quick**: `geoips-base` plus the editable developer extras, without the
  plugin packages
* **production**: minimal runtime image without source tree, Ansible or
  compilers

See {ref}`docker-builds` for the full stage and build-argument reference.

(dev-container)=

## Dev Container

The repository ships a VS Code Dev Containers / `devcontainer` CLI
configuration in `.devcontainer/`. It builds the `dev` target, mounts your
checkout at `/packages/geoips` (wired to the editable install), mounts the
host test data and output directories, and starts sshd on port 2222 through a
post-start command.

Prerequisites: Docker and the VS Code *Dev Containers* extension (or the
`devcontainer` CLI). Open the repository folder and choose **Dev Containers:
Reopen in Container**, or run:

```{code-block} bash

    devcontainer up --workspace-folder .
```

### Host data directories

Two host directories are mounted into every container:

* `~/.geoips/testdata` → `/geoips_testdata` (`GEOIPS_TESTDATA_DIR`, which is
  also the ancillary data root `GEOIPS_ANCILDAT`)
* `~/.geoips/output` → `/output` (`GEOIPS_OUTDIRS`)

The mount sources are fixed at `$HOME/.geoips/...`, because the devcontainer
substitution engine only resolves one level of `${...}`. To keep the data
somewhere else, export `GEOIPS_TESTDATA_DIR` / `GEOIPS_OUTDIRS` in the
environment that launches the container: before the container starts,
`.devcontainer/initialize.sh` creates the directory the variable points at and
turns `~/.geoips/testdata` (or `~/.geoips/output`) into a symlink to it. An
existing symlink is repointed, an existing *empty* directory is replaced, and
a non-empty real directory is left alone with a warning on stderr. With the
variables unset the two `~/.geoips` directories are created and used
directly. The script is idempotent, so re-opening the container is safe.

Cartopy's natural-earth shapefiles are baked into the image by the `deps`
stage (`/packages/shapefiles`, with `CARTOPY_DATA_DIR=/packages`), so they are
not mounted from the host.

### Git worktrees

In a `git worktree` checkout `.git` is a *file* pointing at the main clone's
administrative directory on the host, which does not exist inside the
container. The devcontainer mounts the checkout's grandparent directory at
`/workspaces-root`; the post-create script
(`tests/ansible/scripts/devcontainer-setup.sh`) finds the matching worktree
administrative directory there and — when the host path of that directory is
not visible in the container — creates a symlink from the host prefix to
`/workspaces-root` so git resolves the worktree inside the container as well.
The script never rewrites the mounted `.git`, so the host checkout keeps
working; it also adds the workspace to git's `safe.directory` list. Plain
clones (a `.git` directory) need no handling.

### SSH access

`openssh-server` is installed and `sshd` is started on port 2222, which the
editor forwards silently. Log in as `geoips_user` with the keys in your host
`~/.ssh/authorized_keys`:

```{code-block} bash

    ssh -p 2222 geoips_user@localhost
```

Root login, password authentication and keyboard-interactive authentication
are disabled. `geoips_user` has passwordless `sudo` (needed to start sshd).

### Private plugins

To build the image with the private plugin repositories, export a GitHub token
with read access to them and enable the plugins before the container is
created or rebuilt:

```{code-block} bash

    export GEOIPS_PRIVATE_TOKEN=<token>
    export GEOIPS_USE_PRIVATE_PLUGINS=true
```

`.devcontainer/initialize.sh` writes the token to `~/.geoips/github-token`
with mode `0600`, and the devcontainer passes that file as the
`geoips_private_token` BuildKit secret, so the token never ends up in an image
layer or the image history. If `GEOIPS_PRIVATE_TOKEN` is unset the script
reuses the token file documented in
`tests/ansible/README.md`, `~/.config/geoips/github-token`; if neither exists
it writes an empty token file, so the build still succeeds with the public
plugins only. `GEOIPS_USE_PRIVATE_PLUGINS` defaults to `false` — never push an
image built with it set to `true` to a public registry, because it contains the
private plugins' source.

The container's Python interpreter is `/usr/local/bin/python` — every install
uses `uv pip install --system`, so nothing lives in `geoips_user`'s home
directory. Linting comes from the flake8 extension and formatting from the
black formatter.

# Test Data Requirements

Developers need test data repositories in $GEOIPS_TESTDATA_DIR for tests to
pass. This is automatically handled by the installation scripts but requires
significant disk space and download time.

**Important**: Test data is only required for development. Users installing via pip do not need test data.

[geoips_github]: https://github.com/NRLMMD-GEOIPS/geoips
[mamba]: https://mamba.readthedocs.io/en/latest/
[miniconda]: https://docs.conda.io/en/latest/miniconda.html
[anaconda]: https://www.anaconda.com/products/distribution
