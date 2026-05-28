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
#  Extra plugins (any target):
#    docker build --target geoips-site --build-arg EXTRA_PLUGINS=my_plugin .
#
#  Private plugins:
#    docker build --target geoips-site --build-arg GEOIPS_USE_PRIVATE_PLUGINS=true .
#
#  Test data is NEVER baked in.  Mount at runtime:
#    docker run -v /path/to/testdata:/geoips_testdata geoips ...
# =============================================================================

###############################################################################
# Stage 1: base-os — system packages only, no Python libs
###############################################################################
FROM python:3.11-slim-trixie AS base-os

ARG DEBIAN_FRONTEND=noninteractive
ENV CFLAGS="-Wno-incompatible-pointer-types"
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
       git wget libopenblas-dev g++ make gfortran \
       libeccodes-dev \
    && echo "deb http://deb.debian.org/debian/ unstable main contrib non-free" | tee /etc/apt/sources.list.d/unstable.list \
    && apt-get update \
    && apt install -y -t unstable gdal-bin libgdal-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip

###############################################################################
# Stage 2: deps — Python requirements cached separately from source changes
#
# This layer only rebuilds when requirements.txt changes, so day-to-day
# source edits skip the slow dependency download entirely.
###############################################################################
FROM base-os AS deps

ARG USER=geoips_user
ARG USER_ID=1000
ARG GROUP_ID=1000

ENV GEOIPS_PACKAGES_DIR=/packages \
    GEOIPS_OUTDIRS=/output \
    GEOIPS_TESTDATA_DIR=/geoips_testdata \
    GEOIPS_DEPENDENCIES_DIR=/app/dependencies \
    GEOIPS_REPO_URL=https://github.com/NRLMMD-GEOIPS/ \
    CARTOPY_DATA_DIR=/packages

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

# ---- cached layer: only rebuilds when requirements.txt changes ----
# ansible-core is a build-time tool only (stripped in production) so it
# keeps its wheel for speed.
COPY --chown=${USER}:${GROUP_ID} environments/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && pip install --no-cache-dir ansible-core

###############################################################################
# Stage 3: geoips-base — core GeoIPS built from source (non-editable)
###############################################################################
FROM deps AS geoips-base

ARG USER=geoips_user
ARG USER_ID=1000
ARG GROUP_ID=1000
ARG EXTRA_PLUGINS=""
ARG GEOIPS_MODIFIED_BRANCH=""

ENV EXTRA_PLUGINS=${EXTRA_PLUGINS} \
    GEOIPS_MODIFIED_BRANCH=${GEOIPS_MODIFIED_BRANCH}

# ---- this layer rebuilds on any source change, but deps above are cached ----
# .git is excluded via .dockerignore — the image is smaller and worktree-safe.
COPY --chown=${USER}:${GROUP_ID} . ${GEOIPS_PACKAGES_DIR}/geoips/

RUN git config --global --add safe.directory '*'

RUN cd ${GEOIPS_PACKAGES_DIR}/geoips/tests/ansible \
    && ansible-playbook playbooks/install.yml \
      --tags base \
      -e pip_editable=false \
      -v \
    && chown -R ${USER_ID}:${GROUP_ID} ${GEOIPS_PACKAGES_DIR} /home/${USER}

###############################################################################
# Stage 4: geoips-full — shapefiles, settings repos, doc/test extras
###############################################################################
FROM geoips-base AS geoips-full

ARG USER=geoips_user
ARG USER_ID=1000
ARG GROUP_ID=1000

USER root
RUN cd ${GEOIPS_PACKAGES_DIR}/geoips/tests/ansible \
    && ansible-playbook playbooks/install.yml \
      --tags full \
      -e pip_editable=false \
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
ENV GEOIPS_USE_PRIVATE_PLUGINS=${GEOIPS_USE_PRIVATE_PLUGINS}

USER root
RUN cd ${GEOIPS_PACKAGES_DIR}/geoips/tests/ansible \
    && ansible-playbook playbooks/install.yml \
      --tags site \
      -e pip_editable=false \
      -v \
    && chown -R ${USER_ID}:${GROUP_ID} ${GEOIPS_PACKAGES_DIR} ${GEOIPS_OUTDIRS} /home/${USER}

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
RUN cd ${GEOIPS_PACKAGES_DIR}/geoips \
    && pip install --no-cache-dir -e '.[doc,test,lint,debug]'

# Re-run ansible install for all plugin repos in editable mode so
# their source trees (mounted or COPY'd) are also editable.
# Skip registries — devs regenerate them as needed.
RUN cd ${GEOIPS_PACKAGES_DIR}/geoips/tests/ansible \
    && ansible-playbook playbooks/install.yml \
      --tags site \
      -e pip_editable=true \
      --skip-tags registries \
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

RUN cd ${GEOIPS_PACKAGES_DIR}/geoips \
    && pip install --no-cache-dir -e '.[doc,test,lint,debug]'

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
