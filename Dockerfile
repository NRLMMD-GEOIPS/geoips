# Usage:
#
# To use this for production, you will need to mount your input data directory and your
# output directory.
#
# To use this for running the integration tests, you will need to mount in the test data
# directory. It would likely also be good to mount in an output data directory. This can
# be either persistent (i.e. from your system) or volatile.
#
# To use this for development, you will want to re-build the image from the Dockerfile
# with two build-args, USER_ID and GROUP_ID set to your personal user id and group id.
# When running the image for development, you should mount in your $GEOIPS_PACKAGES_DIR
# to /app/geoips_packages, mount your output directory to /output, and mount your test
# data directory to /data.

FROM python:3.10-slim-bullseye as gdal

# First stage installs gdal

RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y apt-file software-properties-common # wget git libopenblas-dev g++ make

RUN add-apt-repository -y ppa:ubuntugis/ppa && \
    apt-get install -y gdal-bin libgdal-dev && \
    mkdir /hard-links && \
    for fn in $(dpkg -L gdal-bin libgdal-dev); do if [[ -f $fn ]]; then mkdir -p /hard-links/$(dirname $fn); ln $fn /hard-links/${fn}; fi; done

FROM python:3.10-slim-bullseye as env_setup

# Second stage installs base GeoIPS

COPY --from=gdal /hard-links /hard-links
RUN for fn in $(find /hard-links -type f); do nfn=${fn#/hard-links/}; mkdir -p $(dirname $nfn); ln $fn $nfn; done

RUN apt-get update && \
    apt-get -y install wget git libopenblas-dev && \
    rm -rf /var/lib/apt/lists/*

ARG GEOIPS_PACKAGES_DIR=/app/geoips_packages

WORKDIR $GEOIPS_PACKAGES_DIR

ARG USER=geoips_user
# ARG GROUP=${USER}
ARG USER_ID=25000
ARG GROUP_ID=25000

RUN getent group ${GROUP_ID} > /dev/null || groupadd -g ${GROUP_ID} ${USER} \
    && useradd --gid ${GROUP_ID} --uid ${USER_ID} -l -m ${USER}

ARG GEOIPS_REPO_URL=https://github.com/NRLMMD-GEOIPS/geoips.git
ARG GEOIPS_OUTDIRS=/output
ARG GEOIPS_DEPENDENCIES_DIR=/data
ARG GEOIPS_TESTDATA_DIR=/data

RUN mkdir -p /build /wheels $GEOIPS_OUTDIRS $GEOIPS_DEPENDENCIES_DIR $GEOIPS_TESTDATA_DIR
RUN chown ${USER_ID}:${GROUP_ID} /build /wheels $GEOIPS_OUTDIRS $GEOIPS_DEPENDENCIES_DIR $GEOIPS_TESTDATA_DIR

USER ${USER}

ENV PATH=${PATH}:/home/${USER}/.local/bin:${GEOIPS_DEPENDENCIES_DIR}/bin
ENV GEOIPS_REPO_URL=${GEOIPS_REPO_URL}
ENV GEOIPS_OUTDIRS=${GEOIPS_OUTDIRS}
ENV GEOIPS_PACKAGES_DIR=${GEOIPS_PACKAGES_DIR}
ENV GEOIPS_DEPENDENCIES_DIR=${GEOIPS_DEPENDENCIES_DIR}
ENV GEOIPS_TESTDATA_DIR=${GEOIPS_TESTDATA_DIR}

FROM env_setup as install
WORKDIR ${GEOIPS_PACKAGES_DIR}/geoips

# Mount in GeoIPS and build wheels for it and its dependencies
RUN --mount=type=bind,source=.,target=/build/geoips \
    cp -r /build/geoips ${GEOIPS_PACKAGES_DIR} && \
    pip wheel --no-cache-dir --no-cache --wheel-dir /wheels . && \
    rm -rf /build/*

FROM env_setup as test

WORKDIR ${GEOIPS_PACKAGES_DIR}/geoips

# Mount in wheels from previous step
# Mount in GeoIPS
# Install wheels
# Install GeoIPS in editable mode
RUN --mount=type=bind,from=install,source=/wheels,target=/wheels \
    --mount=type=bind,source=.,target=${GEOIPS_PACKAGES_DIR}/geoips \
    pip install --no-cache /wheels/* && \
    git config --global --add safe.directory $PWD && \
    pip install .[doc,lint,test]

FROM env_setup as prod

# Mount in wheels from previous stage
# Install wheels (includes GeoIPS)
RUN --mount=type=bind,from=install,source=/wheels,target=/wheels \
    pip install --no-cache /wheels/*
