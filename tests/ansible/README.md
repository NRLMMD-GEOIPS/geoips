# GeoIPS Ansible Installation

Ansible roles that replace the legacy `base_install.sh`, `full_install.sh`,
`site_install.sh`, and `check_system_requirements.sh` scripts.

## Tiers

| Tag    | What it does                                                        |
|--------|---------------------------------------------------------------------|
| `base` | Installs GeoIPS core (`pip install -e .`), creates registries       |
| `full` | Adds cartopy shapefiles, settings repos, doc/test extras            |
| `site` | Adds all open-source plugin packages (fortran chain, geocolor, …)   |

Tags are additive — always include all lower tiers:

```bash
# Base only
ansible-playbook tests/ansible/playbooks/install.yml --tags base

# Full (includes base tasks too)
ansible-playbook tests/ansible/playbooks/install.yml --tags base,full

# Site (includes base + full)
ansible-playbook tests/ansible/playbooks/install.yml --tags base,full,site
```

## Extra variables

| Variable                       | Default | Description                                  |
|-------------------------------|---------|----------------------------------------------|
| `pip_editable`                | `true`  | `true` = editable dev install; `false` = build from source (smaller image) |
| `pip_extra_args`              | `""`    | Extra args for pip (Dockerfile uses `--no-binary :all:`) |
| `geoips_use_private_plugins`  | `false` | Include proprietary repos (ryglickicane, …)  |
| `extra_plugins`               | `""`    | Comma-separated list of additional repo names |
| `geoips_modified_branch`      | `""`    | Branch to checkout after cloning each repo    |

Pass with `-e`:

```bash
ansible-playbook tests/ansible/playbooks/install.yml --tags base,full,site \
  -e geoips_use_private_plugins=true \
  -e extra_plugins=my_plugin,other_plugin
```

## Docker builds

The Dockerfile uses a `deps` stage that installs `requirements.txt` in its
own layer.  Day-to-day source changes skip the slow dependency download
entirely because Docker caches that layer.

All Docker stages pass `-e pip_editable=false` so packages are built from
source into `site-packages`.  They also pass `-e 'pip_extra_args=--no-binary
:all:'` so every Python dependency is compiled from source inside the
container rather than using pre-built wheels.  This produces binaries
optimised for the target architecture and avoids wheel bloat.  The `deps`
stage applies the same flag to `requirements.txt`, and that layer is cached
so rebuilds only happen when requirements change.

```bash
# Base image (smallest, core GeoIPS only)
docker build --target geoips-base -t geoips:base .

# Full image
docker build --target geoips-full -t geoips:full .

# Site image with a custom plugin
docker build --target geoips-site -t geoips:site \
  --build-arg EXTRA_PLUGINS=my_custom_plugin .

# Production (no source, no ansible, no git)
docker build --target production -t geoips:prod .

# Run tests (test data mounted, never baked in)
docker run --rm -v /data/testdata:/geoips_testdata geoips:full \
  pytest -m "base and integration"
```

## Roles

```
roles/
├── system_deps/          # Verifies git, python, compilers are present
├── python_env/           # pip install geoips (core, extras)
├── cartopy_shapefiles/   # natural-earth-vector clone + symlinks
├── settings_repos/       # .vscode, .github, geoips_ci
├── source_repos/         # Plugin packages — clone + pip install -e
├── test_data/            # Download test datasets via geoips config install
└── registries/           # geoips config create-registries
```

## Prerequisites

```bash
pip install ansible-core
```

No other Ansible collections required — only `ansible.builtin` modules are used.

## Test data

Test data is managed by a **separate playbook** (`test_data.yml`) and is
**never baked into Docker images**.  The `test_data` role calls
`geoips config install` for each dataset, which is idempotent — cached
data on disk is a fast no-op.

### Bare metal

```bash
# Download base datasets
cd tests/ansible && ansible-playbook playbooks/test_data.yml --tags base

# Download base + full datasets
cd tests/ansible && ansible-playbook playbooks/test_data.yml --tags base,full

# Everything including site + private
cd tests/ansible && ansible-playbook playbooks/test_data.yml --tags base,full,site \
  -e geoips_use_private_plugins=true

# Override download location
cd tests/ansible && ansible-playbook playbooks/test_data.yml --tags base \
  -e geoips_testdata_dir=/my/custom/path
```

### Docker (download to host, mount at runtime)

The ansible playbook runs **inside** the container with the testdata
directory mounted as a volume, so downloads persist on the host:

```bash
# Download base + full datasets to host
make testdata-full TESTDATA=/data/geoips-testdata

# Then run tests with that data mounted
docker run --rm -v /data/geoips-testdata:/geoips_testdata geoips:full \
  pytest -m "base and integration"
```

### CI

The CI workflow has a dedicated `test-data` job that runs in parallel with
lint/unit tests.  It runs the ansible `test_data.yml` playbook inside the
Docker container with a host volume, so on self-hosted runners the data is
cached between runs.  The `integration` job depends on `test-data` and
mounts the same volume.
