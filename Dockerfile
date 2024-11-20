FROM python:3.11-bullseye

RUN apt-get update && apt-get -y upgrade \ 
    && apt-get install -y wget git libopenblas-dev imagemagick g++ make gfortran \
    && apt-get update && apt-get install -y software-properties-common \
    && add-apt-repository -y ppa:ubuntugis/ppa \
    && apt-get install -y gdal-bin libgdal-dev \
    && pip install -U pip

ARG GEOIPS_PACKAGES_DIR=/app/geoips_packages

WORKDIR $GEOIPS_PACKAGES_DIR

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
    && mkdir -p $GEOIPS_OUTDIRS $GEOIPS_DEPENDENCIES_DIR $GEOIPS_TESTDATA_DIR /data /docker_data \
    && chown ${USER_ID}:${GROUP_ID} $GEOIPS_OUTDIRS $GEOIPS_DEPENDENCIES_DIR $GEOIPS_TESTDATA_DIR $GEOIPS_PACKAGES_DIR /data

USER ${USER}

WORKDIR $GEOIPS_PACKAGES_DIR

COPY --chown=${USER_ID}:${GROUP_ID} ./environments/requirements.txt ${GEOIPS_PACKAGES_DIR}/requirements.txt

RUN python3 -m pip install rasterio \
    && python3 -m pip install numpy==1.26.4 && python3 -m pip install -r requirements.txt 

# For akima86
#USER root
#RUN git clone --single-branch -b 3-build-fails-up-to-date-setuptools https://github.com/NRLMMD-GEOIPS/akima86.git && cd akima86 && python3 setup.py install
#USER ${USER}

COPY --chown=${USER_ID}:${GROUP_ID} . ${GEOIPS_PACKAGES_DIR}/geoips

WORKDIR ${GEOIPS_PACKAGES_DIR}/geoips
RUN cd ${GEOIPS_PACKAGES_DIR}/geoips \
    && pip install -e "$GEOIPS_PACKAGES_DIR/geoips[test, doc, lint, debug]" \
    && create_plugin_registries
