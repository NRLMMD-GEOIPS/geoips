FROM python:3.10-slim-bullseye

RUN apt-get update && apt-get -y upgrade
# RUN apt-get install -y wget git libopenblas-dev imagemagick g++ make
RUN apt-get install -y wget git libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# RUN apt-get update && apt-get install -y software-properties-common
# RUN add-apt-repository -y ppa:ubuntugis/ppa
# RUN apt-get install -y gdal-bin libgdal-dev
RUN pip install --no-cache-dir -U pip

# # could install the rest of geoips dependancies here
# RUN pip install rasterio

# When transitioning to a multistage build, this is the end of the first build

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

RUN mkdir -p $GEOIPS_OUTDIRS $GEOIPS_DEPENDENCIES_DIR $GEOIPS_TESTDATA_DIR
RUN chown ${USER_ID}:${GROUP_ID} $GEOIPS_OUTDIRS $GEOIPS_DEPENDENCIES_DIR $GEOIPS_TESTDATA_DIR

USER ${USER}

ENV PATH=${PATH}:/home/${USER}/.local/bin:${GEOIPS_DEPENDENCIES_DIR}/bin
ENV GEOIPS_REPO_URL=${GEOIPS_REPO_URL}
ENV GEOIPS_OUTDIRS=${GEOIPS_OUTDIRS}
ENV GEOIPS_PACKAGES_DIR=${GEOIPS_PACKAGES_DIR}
ENV GEOIPS_DEPENDENCIES_DIR=${GEOIPS_DEPENDENCIES_DIR}
ENV GEOIPS_TESTDATA_DIR=${GEOIPS_TESTDATA_DIR}

COPY --chown=${USER_ID}:${GROUP_ID} . ${GEOIPS_PACKAGES_DIR}/geoips/

WORKDIR ${GEOIPS_PACKAGES_DIR}/geoips
RUN cd ${GEOIPS_PACKAGES_DIR}/geoips \
    && pip install --no-cache-dir -e "$GEOIPS_PACKAGES_DIR/geoips[test,doc,lint]" \
    && create_plugin_registries
