# =============================================================================
#  GeoIPS Multi-Stage Dockerfile
#
#  Build targets:
#    docker build --target geoips-base .     # core GeoIPS only
#    docker build --target geoips-full .     # + shapefiles, settings repos, doc/test extras
#    docker build --target geoips-site .     # + all open-source plugin packages
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
# Set compiler flags to work around pyhdf's outdated C wrapper
ENV CFLAGS="-Wno-incompatible-pointer-types"
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
       git wget libopenblas-dev g++ make gfortran\
# for pygrib
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
# --no-binary :all: compiles every dependency from source so the resulting
# binaries are optimised for the container's architecture and the image
# carries no pre-built wheel bloat.  ansible-core is a build-time tool
# only (stripped in production) so it keeps its wheel for speed.
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
COPY --chown=${USER}:${GROUP_ID} . ${GEOIPS_PACKAGES_DIR}/geoips/

RUN git config --global --add safe.directory '*'

# Build from source (non-editable).  The package lands in site-packages,
# which keeps the image smaller than an editable install that symlinks
# the entire source tree.  --no-binary :all: ensures every dependency is
# compiled from source (requirements.txt deps were already built in the
# deps stage, so this is a fast no-op for those).
#
# cd into the ansible directory so ansible.cfg is found automatically and
# roles_path=roles resolves to tests/ansible/roles/.
RUN cd ${GEOIPS_PACKAGES_DIR}/geoips/tests/ansible \
    && ansible-playbook playbooks/install.yml \
      --tags base \
      -e pip_editable=false \
#      -e 'pip_extra_args=--no-binary :all:' \
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
#      -e 'pip_extra_args=--no-binary :all:' \
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
#      -e 'pip_extra_args=--no-binary :all:' \
      -v \
    && chown -R ${USER_ID}:${GROUP_ID} ${GEOIPS_PACKAGES_DIR} ${GEOIPS_OUTDIRS} /home/${USER}

USER ${USER}

###############################################################################
# Stage 5: geoips-dev — site + dev packages (eg. ssh, git, etc.)
###############################################################################
FROM geoips-site AS dev

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
#      -e 'pip_extra_args=--no-binary :all:' \
      -v \
    && chown -R ${USER_ID}:${GROUP_ID} ${GEOIPS_PACKAGES_DIR} ${GEOIPS_OUTDIRS} /home/${USER}


USER ${USER}

###############################################################################
# Stage 6: production — minimal runtime, no source tree, no ansible, no git
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
