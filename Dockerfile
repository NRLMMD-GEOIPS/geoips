FROM python:3.10-slim-bullseye AS base

RUN apt-get update && apt-get -y upgrade \
    && apt-get install -y wget git libopenblas-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -U pip

FROM base AS doclinttest

ARG GEOIPS_PACKAGES_DIR=/app/geoips_packages

WORKDIR $GEOIPS_PACKAGES_DIR

ARG GEOIPS_OUTDIRS=/output
ENV GEOIPS_OUTDIRS=${GEOIPS_OUTDIRS}

ARG USER=geoips_user
ARG GROUP=${USER}
ARG USER_ID=10039
ARG GROUP_ID=100

ARG GEOIPS_REPO_URL=https://github.com/NRLMMD-GEOIPS/
ARG GEOIPS_OUTDIRS=/output
ARG GEOIPS_DEPENDENCIES_DIR=/mnt/dependencies
ARG GEOIPS_TESTDATA_DIR=/mnt/geoips_testdata

ENV PATH=${PATH}:/home/${USER}/.local/bin:${GEOIPS_DEPENDENCIES_DIR}/bin
ENV GEOIPS_REPO_URL=${GEOIPS_REPO_URL}
ENV GEOIPS_OUTDIRS=${GEOIPS_OUTDIRS}
ENV GEOIPS_PACKAGES_DIR=${GEOIPS_PACKAGES_DIR}
ENV CARTOPY_DATA_DIR=${GEOIPS_PACKAGES_DIR}
ENV GEOIPS_DEPENDENCIES_DIR=${GEOIPS_DEPENDENCIES_DIR}
ENV GEOIPS_TESTDATA_DIR=${GEOIPS_TESTDATA_DIR}

RUN getent group ${GROUP_ID} > /dev/null || groupadd -g ${GROUP_ID} ${USER} \
    && useradd --gid ${GROUP_ID} --uid ${USER_ID} -l -m ${USER} \
    && mkdir -p $GEOIPS_OUTDIRS $GEOIPS_DEPENDENCIES_DIR $GEOIPS_TESTDATA_DIR /data /__w\
    && chown ${USER_ID}:${GROUP_ID} $GEOIPS_OUTDIRS $GEOIPS_DEPENDENCIES_DIR $GEOIPS_TESTDATA_DIR $GEOIPS_PACKAGES_DIR /data /__w

#USER ${USER}
WORKDIR $GEOIPS_PACKAGES_DIR

COPY --chown=${USER_ID}:${GROUP_ID} ./environments/requirements.txt ${GEOIPS_PACKAGES_DIR}/requirements.txt

RUN python3 -m pip install -r requirements.txt

WORKDIR ${GEOIPS_PACKAGES_DIR}/geoips
COPY --chown=${USER_ID}:${GROUP_ID} . .

RUN pip install -e ".[test, doc, lint]" \
    && create_plugin_registries
