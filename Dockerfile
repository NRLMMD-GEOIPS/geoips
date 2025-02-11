FROM python:3.10-slim-bullseye AS base

RUN apt-get update && apt-get -y upgrade \
    && apt-get install -y wget git libopenblas-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -U pip

FROM base AS doclinttest

ARG GEOIPS_PACKAGES_DIR=/packages

WORKDIR $GEOIPS_PACKAGES_DIR

ARG GEOIPS_OUTDIRS=/output
ENV GEOIPS_OUTDIRS=${GEOIPS_OUTDIRS}

ARG GEOIPS_REPO_URL=https://github.com/NRLMMD-GEOIPS/
ARG GEOIPS_OUTDIRS=/output
ARG GEOIPS_DEPENDENCIES_DIR=/mnt/dependencies
ARG GEOIPS_TESTDATA_DIR=/mnt/geoips_testdata

ENV PATH=${PATH}:/home/root/.local/bin:${GEOIPS_DEPENDENCIES_DIR}/bin
ENV GEOIPS_REPO_URL=${GEOIPS_REPO_URL}
ENV GEOIPS_OUTDIRS=${GEOIPS_OUTDIRS}
ENV GEOIPS_PACKAGES_DIR=${GEOIPS_PACKAGES_DIR}
ENV CARTOPY_DATA_DIR=${GEOIPS_PACKAGES_DIR}
ENV GEOIPS_DEPENDENCIES_DIR=${GEOIPS_DEPENDENCIES_DIR}
ENV GEOIPS_TESTDATA_DIR=${GEOIPS_TESTDATA_DIR}

RUN mkdir -p $GEOIPS_OUTDIRS $GEOIPS_DEPENDENCIES_DIR $GEOIPS_TESTDATA_DIR

WORKDIR $GEOIPS_PACKAGES_DIR

COPY ./environments/requirements.txt ${GEOIPS_PACKAGES_DIR}/requirements.txt

RUN python3 -m pip install -r requirements.txt

WORKDIR ${GEOIPS_PACKAGES_DIR}/geoips
COPY . .

RUN pip install -e ".[test, doc, lint]" \
    && create_plugin_registries
