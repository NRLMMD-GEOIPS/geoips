# =============================================================================
#  GeoIPS Multi-Stage Dockerfile
#
#  Build targets:
#    docker build --target geoips-base .     # core GeoIPS only
#    docker build --target geoips-full .     # + shapefiles, settings repos, doc/test extras
#    docker build --target geoips-site .     # + all open-source plugin packages
#    docker build --target dev .             # site + editable install + dev tools (ssh,vim,…)
#    docker build --target dev-quick .       # base + editable install + dev tools (fast build)
#    docker build --target production  .     # slim runtime image (no source, no ansible)
#
#  Cache-optimised CI usage:
#    # 1. Pull/push deps cache across runs (deps stage changes rarely)
#    docker build --target deps --tag geoips:cache .
#    docker push ghcr.io/org/repo:build-cache
#
#    # 2. Build full target using cached deps layers
#    docker build --cache-from geoips:cache --target geoips-site --tag $IMAGE_TAG .
#
#  Extra plugins (any target):
#    docker build --target geoips-site --build-arg EXTRA_PLUGINS=my_plugin .
#
#  Testing against other branches (geoips-site; geoips_ci sets these from
#  .github/ci-dependencies.yaml). REPO_BRANCHES: "repo=ref ..." to clone those repos
#  at a branch, tag or commit. PIP_OVERRIDES: pip requirements, one per line,
#  installed last so they replace the pinned versions:
#    docker build --target geoips-site --build-arg REPO_BRANCHES="recenter_tc=my-fix" \
#        --build-arg PIP_OVERRIDES="pluginify @ git+https://github.com/NRLMMD-GEOIPS/pluginify@my-fix" .
#
#  Disabled plugin repos (geoips_ci sets this from .github/ci-disabled-repos.yaml).
#  DISABLED_REPOS: "repo repo ..." to leave those plugin repos out of the install:
#    docker build --target geoips-site --build-arg DISABLED_REPOS="synth_green" .
#
#  Private plugins (needs a GitHub token that can read the private repos, given
#  as a BuildKit secret; it never ends up in an image layer or the history):
#    docker build --target geoips-site --build-arg GEOIPS_USE_PRIVATE_PLUGINS=true \
#        --secret id=geoips_private_token,src=/path/to/token-file .
#  See tests/ansible/scripts/github-token-env.sh.  Do not push such an image to a
#  public registry: it contains the private plugins' source.
#
#  Test data is NEVER baked in.  Mount at runtime:
#    docker run -v /path/to/testdata:/geoips_testdata geoips ...
# =============================================================================

###############################################################################
# Stage 1: base-os — system packages + uv (no Python libs yet)
###############################################################################
FROM python:3.11-slim-trixie AS base-os

ARG DEBIAN_FRONTEND=noninteractive
ENV CFLAGS="-Wno-incompatible-pointer-types"

# Single apt pass: add unstable source first, then one update + install.
RUN echo "deb http://deb.debian.org/debian/ unstable main contrib non-free" \
      > /etc/apt/sources.list.d/unstable.list \
    && apt-get update --error-on=any \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        git wget libopenblas-dev g++ make gfortran libeccodes-dev \
        gdal-bin/unstable libgdal-dev/unstable \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

###############################################################################
# Stage 2: deps — Python requirements + cartopy shapefiles (cached layer)
#
# Everything below the ---- line only rebuilds when requirements.txt or the
# shapefiles setup changes.  Day-to-day source edits skip this entire stage.
###############################################################################
FROM base-os AS deps

ARG USER=geoips_user
ARG USER_ID=1000
ARG GROUP_ID=1000

ENV GEOIPS_PACKAGES_DIR=/packages \
    GEOIPS_OUTDIRS=/output \
    GEOIPS_TESTDATA_DIR=/geoips_testdata \
    GEOIPS_ANCILDAT = /geoips_testdata \
    GEOIPS_DEPENDENCIES_DIR=/app/dependencies \
    GEOIPS_REPO_URL=https://github.com/NRLMMD-GEOIPS/ \
    CARTOPY_DATA_DIR=/packages \
    PIP_ROOT_USER_ACTION=ignore

RUN groupadd -g ${GROUP_ID} ${USER} \
    && useradd -l -m -u ${USER_ID} -g ${GROUP_ID} ${USER} \
    && mkdir -p \
       ${GEOIPS_OUTDIRS} \
       ${GEOIPS_DEPENDENCIES_DIR} \
       ${GEOIPS_TESTDATA_DIR} \
       ${GEOIPS_PACKAGES_DIR}/geoips \
    && chown -R ${USER}:${GROUP_ID} \
       ${GEOIPS_OUTDIRS} \
       ${GEOIPS_DEPENDENCIES_DIR} \
       ${GEOIPS_TESTDATA_DIR} \
       ${GEOIPS_PACKAGES_DIR}

# ---- cached layer: Python packages (changes only when requirements.txt does) ----
COPY --chown=${USER}:${GROUP_ID} environments/requirements.txt /tmp/requirements.txt
RUN uv pip install --system --no-cache -r /tmp/requirements.txt \
    && uv pip install --system --no-cache ansible-core

# ---- cached layer: cartopy shapefiles (no source dependency) ----
# Pre-populated here so the ansible role in later stages detects them and skips.
# This clone is 300MB+ and only reruns when the Dockerfile line changes.
RUN git clone --depth 1 https://github.com/nvkelso/natural-earth-vector \
      /packages/shapefiles_clone/natural-earth-vector \
    && mkdir -p /packages/shapefiles/natural_earth/cultural \
               /packages/shapefiles/natural_earth/physical \
    && ln -sfv /packages/shapefiles_clone/natural-earth-vector/*_cultural/*/* \
               /packages/shapefiles/natural_earth/cultural/ \
    && ln -sfv /packages/shapefiles_clone/natural-earth-vector/*_physical/*/* \
               /packages/shapefiles/natural_earth/physical/ \
    && ln -sfv /packages/shapefiles_clone/natural-earth-vector/*_cultural/* \
               /packages/shapefiles/natural_earth/cultural/ \
    && ln -sfv /packages/shapefiles_clone/natural-earth-vector/*_physical/* \
               /packages/shapefiles/natural_earth/physical/ \
    && chown -R ${USER}:${GROUP_ID} /packages/shapefiles*

###############################################################################
# Stage 3: geoips-base — core GeoIPS built from source (non-editable)
###############################################################################
FROM deps AS geoips-base

ARG USER=geoips_user
ARG USER_ID=1000
ARG GROUP_ID=1000
ARG EXTRA_PLUGINS=""

ENV EXTRA_PLUGINS=${EXTRA_PLUGINS} \
    PIP_ROOT_USER_ACTION=ignore

# ---- this layer rebuilds on any source change, but deps above are cached ----
COPY --chown=${USER}:${GROUP_ID} . ${GEOIPS_PACKAGES_DIR}/geoips/

# Git worktrees store .git as a FILE pointing to the main repo on the host.
# That path is invalid inside the container, which breaks poetry-dynamic-versioning
# (dunamai needs a real .git dir to resolve the version).  Create a minimal shim
# so pip install succeeds.
RUN if [ -f ${GEOIPS_PACKAGES_DIR}/geoips/.git ]; then \
      rm ${GEOIPS_PACKAGES_DIR}/geoips/.git ; \
      cd ${GEOIPS_PACKAGES_DIR}/geoips ; \
      git init -q ; \
      git commit --allow-empty -q -m "docker-build" ; \
    fi

RUN git config --global --add safe.directory '*'

# Install geoips core with uv.  python_env role is skipped because uv already
# installed the package; ansible only runs system_deps verification + registries.
RUN uv pip install --system --no-cache ${GEOIPS_PACKAGES_DIR}/geoips \
    && cd ${GEOIPS_PACKAGES_DIR}/geoips/tests/ansible \
    && ansible-playbook playbooks/install.yml \
       --tags base \
       --skip-tags python_env \
       -e editable_pip_install=false \
       -v \
    && chown -R ${USER_ID}:${GROUP_ID} ${GEOIPS_PACKAGES_DIR} /home/${USER}

###############################################################################
# Stage 3.5: doclinttest - installs doc/lint/test extras for docs + lint CI
###############################################################################
FROM geoips-base AS doclinttest

ARG USER=geoips_user
ARG USER_ID=1000
ARG GROUP_ID=1000

USER root
ENV PIP_ROOT_USER_ACTION=ignore
RUN uv pip install --system --no-cache ${GEOIPS_PACKAGES_DIR}/geoips[doc,lint,test] \
    && chown -R ${USER_ID}:${GROUP_ID} ${GEOIPS_PACKAGES_DIR} /home/${USER}

#USER ${USER}

###############################################################################
# Stage 4: geoips-full — settings repos, doc/test extras
#
# Cartopy shapefiles were pre-populated in the deps stage, so the ansible
# cartopy_shapefiles role is skipped.  Doc/test extras are installed with uv.
###############################################################################
FROM geoips-base AS geoips-full

ARG USER=geoips_user
ARG USER_ID=1000
ARG GROUP_ID=1000
# See the top of this file; read by the ansible inventory.
ARG REPO_BRANCHES=""
ARG DISABLED_REPOS=""
ENV PIP_ROOT_USER_ACTION=ignore

USER root
RUN uv pip install --system --no-cache ${GEOIPS_PACKAGES_DIR}/geoips[doc,test] \
    && cd ${GEOIPS_PACKAGES_DIR}/geoips/tests/ansible \
    && ansible-playbook playbooks/install.yml \
       --tags full \
       --skip-tags python_env,cartopy_shapefiles \
       -e editable_pip_install=false \
       -v \
    && chown -R ${USER_ID}:${GROUP_ID} ${GEOIPS_PACKAGES_DIR} /home/${USER}

USER ${USER}

###############################################################################
# Stage 5: geoips-site — all open-source (+ optional private) plugin packages
###############################################################################
FROM geoips-full AS geoips-site

ARG USER=geoips_user
ARG USER_ID=1000
ARG GROUP_ID=1000
ARG GEOIPS_USE_PRIVATE_PLUGINS=false
ARG EDITABLE_PIP_INSTALL=true
ARG REPO_BRANCHES=""
ARG DISABLED_REPOS=""
ENV GEOIPS_USE_PRIVATE_PLUGINS=${GEOIPS_USE_PRIVATE_PLUGINS}

USER root
ENV PIP_ROOT_USER_ACTION=ignore
# The optional geoips_private_token secret authenticates the clones of private
# plugin repos (see github-token-env.sh); it is only mounted for this step.
RUN --mount=type=secret,id=geoips_private_token \
    . ${GEOIPS_PACKAGES_DIR}/geoips/tests/ansible/scripts/github-token-env.sh \
    && uv pip install --system --no-cache \
    $([ "$EDITABLE_PIP_INSTALL" = "true" ] && echo "-e") \
    ${GEOIPS_PACKAGES_DIR}/geoips[doc,test,lint,debug] \
    && cd ${GEOIPS_PACKAGES_DIR}/geoips/tests/ansible \
    && ansible-playbook playbooks/install.yml \
       --tags site \
       --skip-tags python_env,cartopy_shapefiles \
       -e editable_pip_install=$EDITABLE_PIP_INSTALL \
       -v \
    && chown -R ${USER_ID}:${GROUP_ID} ${GEOIPS_PACKAGES_DIR} ${GEOIPS_OUTDIRS} /home/${USER}

# Test-only Python package overrides (see the top of this file), in their own last
# layer so that changing them rebuilds nothing else. Git URLs of private repos use
# the geoips_private_token secret. The packages they changed are recorded in
# .ci_pip_overrides; pip check only warns, as testing against other versions than
# the pinned ones is often the point.
ARG PIP_OVERRIDES=""
RUN --mount=type=secret,id=geoips_private_token \
    if [ -n "$PIP_OVERRIDES" ]; then \
      . ${GEOIPS_PACKAGES_DIR}/geoips/tests/ansible/scripts/github-token-env.sh \
      && printf '%s\n' "$PIP_OVERRIDES" > /tmp/pip-overrides.txt \
      && uv pip freeze --system | sort > /tmp/freeze-before.txt \
      && uv pip install --system --no-cache -r /tmp/pip-overrides.txt \
      && uv pip freeze --system | sort > /tmp/freeze-after.txt \
      && comm -13 /tmp/freeze-before.txt /tmp/freeze-after.txt \
         > ${GEOIPS_PACKAGES_DIR}/.ci_pip_overrides \
      && { pip check || echo "WARNING: the overrides conflict with pinned dependencies"; } \
      && rm /tmp/pip-overrides.txt /tmp/freeze-before.txt /tmp/freeze-after.txt; \
    fi

USER ${USER}

###############################################################################
# Stage 6: dev — full site + editable install + developer tools
#
# Inherits geoips-site (all plugins installed non-editable) then converts
# to editable mode so the devcontainer's workspace bind-mount at
# /packages/geoips makes host source changes live immediately.
#
# .git is provided by the workspace mount (not baked into the image).
###############################################################################
FROM geoips-site AS dev

ARG USER=geoips_user
ARG USER_ID=1000
ARG GROUP_ID=1000

USER root

# Developer tools — ssh server for remote connections, editors, shell niceties
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       openssh-server \
       vim \
       htop \
       curl \
       bash-completion \
    && rm -rf /var/lib/apt/lists/*

# Convert to editable install.  Non-editable packages are already in
# site-packages from the earlier stages; editable overlays them so
# Python loads from /packages/geoips (→ workspace bind mount → host).
# Re-runs the site tag, so private repos (if enabled) need the token again.
RUN --mount=type=secret,id=geoips_private_token \
    . ${GEOIPS_PACKAGES_DIR}/geoips/tests/ansible/scripts/github-token-env.sh \
    && uv pip install --system --no-cache -e ${GEOIPS_PACKAGES_DIR}/geoips[doc,test,lint,debug] \
    && cd ${GEOIPS_PACKAGES_DIR}/geoips/tests/ansible \
    && ansible-playbook playbooks/install.yml \
       --tags site \
       --skip-tags registries,python_env,cartopy_shapefiles \
       -e editable_pip_install=true \
       -v \
    && chown -R ${USER_ID}:${GROUP_ID} ${GEOIPS_PACKAGES_DIR} /home/${USER}

# Prepare SSH for remote dev connections
RUN mkdir -p /var/run/sshd \
    && echo "PermitRootLogin yes" >> /etc/ssh/sshd_config

USER ${USER}

###############################################################################
# Stage 7: dev-quick — base + editable install + dev tools (fast builds)
#
# Lightweight development target for quick iteration.  Skips all plugins,
# shapefiles, and settings repos.  Use when you only need core GeoIPS.
###############################################################################
FROM geoips-base AS dev-quick

ARG USER=geoips_user
ARG USER_ID=1000
ARG GROUP_ID=1000

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       openssh-server \
       vim \
       htop \
       curl \
       bash-completion \
    && rm -rf /var/lib/apt/lists/*

RUN uv pip install --system --no-cache -e ${GEOIPS_PACKAGES_DIR}/geoips[doc,test,lint,debug]

RUN mkdir -p /var/run/sshd \
    && echo "PermitRootLogin yes" >> /etc/ssh/sshd_config

USER ${USER}

###############################################################################
# Stage 8: production — minimal runtime, no source tree, no ansible, no git
#
# Because we built from source (non-editable), the entire geoips package and
# its plugins live in site-packages.  We copy only that plus the bin stubs,
# leaving the source tree, tests, ansible, docs, and build tools behind.
###############################################################################
FROM base-os AS production

ARG USER=geoips_user
ARG USER_ID=1000
ARG GROUP_ID=1000

ENV GEOIPS_PACKAGES_DIR=/packages \
    GEOIPS_OUTDIRS=/output \
    GEOIPS_TESTDATA_DIR=/geoips_testdata \
    GEOIPS_DEPENDENCIES_DIR=/app/dependencies

RUN groupadd -g ${GROUP_ID} ${USER} \
    && useradd -l -m -u ${USER_ID} -g ${GROUP_ID} ${USER} \
    && mkdir -p ${GEOIPS_OUTDIRS} ${GEOIPS_TESTDATA_DIR}

# Only site-packages and console-script stubs — no source tree at all.
# Copies from geoips-base: includes core GeoIPS but NO plugin packages.
# Plugin packages are not needed for a production runtime image.
COPY --from=geoips-base /usr/local/lib/python3.11/site-packages \
                        /usr/local/lib/python3.11/site-packages
COPY --from=geoips-base /usr/local/bin /usr/local/bin

# Strip build-only OS packages
RUN apt-get remove -y git make wget g++ gfortran \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

USER ${USER}
ENTRYPOINT ["geoips"]
CMD ["--help"]
