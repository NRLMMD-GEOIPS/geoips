###############################################################################
#                              BASE STAGE
###############################################################################
FROM python:3.11-slim-bullseye AS base

# Avoid interactive prompts
ARG DEBIAN_FRONTEND=noninteractive

    # Install site dependencies
    RUN apt-get update \
        && apt-get upgrade -y \
        && apt-get install -y --no-install-recommends \
        wget git libopenblas-dev g++ make gfortran \
        && rm -rf /var/lib/apt/lists/*

    # Upgrade pip
    RUN python -m pip install --no-cache-dir --upgrade pip

    ###############################################################################
    #                              BUILD STAGE
    ###############################################################################
    FROM base AS build

    # Build arguments
    ARG USER=geoips_user
    ARG USER_ID=1000
    ARG GROUP_ID=1000
    ARG GEOIPS_BASE_CLONE_DIR=.

    ARG GEOIPS_PACKAGES_DIR=/packages
    ARG GEOIPS_OUTDIRS=/output
    ARG GEOIPS_DEPENDENCIES_DIR=/app/dependencies
    ARG GEOIPS_TESTDATA_DIR=/geoips_testdata
    ARG GEOIPS_REPO_URL=https://github.com/NRLMMD-GEOIPS/

    # If set to something other than "False", will chmod -R a+rw on output dirs
    ARG UNSAFE_PERMS=False

    # Environment variables
    ENV GEOIPS_OUTDIRS="${GEOIPS_OUTDIRS}" \
        GEOIPS_REPO_URL="${GEOIPS_REPO_URL}" \
        GEOIPS_PACKAGES_DIR="${GEOIPS_PACKAGES_DIR}" \
        GEOIPS_DEPENDENCIES_DIR="${GEOIPS_DEPENDENCIES_DIR}" \
        GEOIPS_TESTDATA_DIR="${GEOIPS_TESTDATA_DIR}" \
        CARTOPY_DATA_DIR="${GEOIPS_PACKAGES_DIR}" \
        PATH="${PATH}:/home/${USER}/.local/bin:${GEOIPS_DEPENDENCIES_DIR}/bin"

    # Create a non-root user
    RUN groupadd -g "${GROUP_ID}" "${USER}" \
        && useradd -l -m -u "${USER_ID}" -g "${GROUP_ID}" "${USER}"


    # Create directories; set ownership and permissions to all if UNSAFE_PERMS != "False"
    RUN mkdir -p "${GEOIPS_OUTDIRS}" \
        && mkdir -p "${GEOIPS_DEPENDENCIES_DIR}" \
        && mkdir -p "${GEOIPS_TESTDATA_DIR}" \
        && mkdir -p "${GEOIPS_PACKAGES_DIR}/geoips" \
        && chown -R "${USER}:${GROUP_ID}" \
            "${GEOIPS_OUTDIRS}" \
            "${GEOIPS_DEPENDENCIES_DIR}" \
            "${GEOIPS_TESTDATA_DIR}" \
            "${GEOIPS_PACKAGES_DIR}" \
        && if [ "${UNSAFE_PERMS}" != "False" ]; then \
            chmod -R a+rw \
            "${GEOIPS_OUTDIRS}" \
            "${GEOIPS_DEPENDENCIES_DIR}" \
            "${GEOIPS_TESTDATA_DIR}" \
            "${GEOIPS_PACKAGES_DIR}"; \
        fi

    USER ${USER}

    # Set working directory
    WORKDIR ${GEOIPS_PACKAGES_DIR}/geoips

    # Copy only requirements first to leverage Docker layer caching
    COPY --chown=${USER}:${GROUP_ID} ${GEOIPS_BASE_CLONE_DIR}/environments/requirements.txt ./requirements.txt
    RUN python -m pip install --no-cache-dir -r requirements.txt

    # Now copy all of GeoIPS
    COPY --chown=${USER}:${GROUP_ID} ${GEOIPS_BASE_CLONE_DIR} ./

    # Configure Git (avoid "detected dubious ownership" warnings when mounted)
    RUN git config --global --add safe.directory '*'

    # Install GeoIPS in editable mode
    RUN python -m pip install --no-cache-dir -e "."
    RUN geoips config create-reg

###############################################################################
#                          FULL BUILD STAGE
###############################################################################
FROM build AS full_build

USER root
RUN --mount=type=bind,from=testdata,target=${GEOIPS_TESTDATA_DIR},rw \
    git config --global --add safe.directory '*' \
    && python -m pip install --no-cache-dir -e "$GEOIPS_PACKAGES_DIR/geoips/" \
    && bash $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/base_install.sh \
    && bash $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/full_install.sh \
    && create_plugin_registries \
    && chown -R ${USER}:${GROUP_ID} ${GEOIPS_PACKAGES_DIR} ${GEOIPS_OUTDIRS}

USER ${USER}
###############################################################################
#                          SITE BUILD STAGE
###############################################################################
FROM build AS site_build

# Install all plugins
USER root
RUN --mount=type=bind,from=testdata,target=${GEOIPS_TESTDATA_DIR},rw \
    git config --global --add safe.directory '*' \
    && python -m pip install --no-cache-dir -e "$GEOIPS_PACKAGES_DIR/geoips/" \
    && bash $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/base_install.sh \
    && bash $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/full_install.sh \
    && bash $GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/site_install.sh \
    && create_plugin_registries \
    && chown -R ${USER}:${GROUP_ID} ${GEOIPS_PACKAGES_DIR} ${GEOIPS_OUTDIRS}
USER ${USER}

###############################################################################
#                          BASE TEST STAGE
###############################################################################
FROM build AS test_base

# Install only test + doc extras and no external plugins (minimal test environment)
RUN python -m pip install --no-cache-dir -e "$GEOIPS_PACKAGES_DIR/geoips/[doc,test]" \
    && echo "import coverage; coverage.process_startup()" > ~/.local/lib/python3.11/site-packages/coverage.pth

###############################################################################
#   TEMPORARY FOR CI TESTING - DELETE AFTER UPDATING CI TO USE test_base
###############################################################################
FROM build AS doclinttest

USER root
# Configure Git (avoid "detected dubious ownership" warnings when mounted)
RUN git config --global --add safe.directory '*'

RUN python -m pip install --no-cache-dir -e "$GEOIPS_PACKAGES_DIR/geoips/[doc,lint,test]"

RUN mkdir -p /__w /__e /__t /github && \
    chmod -R 777 /__w /__e /__t /github /tmp # For github actions

# Switch back to non-root for runtime
#USER ${USER}

###############################################################################
#                          FULL TEST STAGE
###############################################################################
FROM full_build AS test_full

RUN python -m pip install --no-cache-dir -e "$GEOIPS_PACKAGES_DIR/geoips/[doc,test]" \
    && echo "import coverage; coverage.process_startup()" > ~/.local/lib/python3.11/site-packages/coverage.pth
# See https://coverage.readthedocs.io/en/coverage-5.1/subprocess.html#measuring-sub-processes
# for more info on how this helps measure coverage of subprocess-based tests

ENTRYPOINT ["pytest"]

###############################################################################
#                          SITE TEST STAGE
###############################################################################
FROM site_build AS test_site

RUN python -m pip install --no-cache-dir -e "$GEOIPS_PACKAGES_DIR/geoips/[doc,test]" \
    && echo "import coverage; coverage.process_startup()" > ~/.local/lib/python3.11/site-packages/coverage.pth
# See https://coverage.readthedocs.io/en/coverage-5.1/subprocess.html#measuring-sub-processes
# for more info on how this helps measure coverage of subprocess-based tests

ENTRYPOINT ["pytest"]

###############################################################################
#                           DEV STAGE
###############################################################################
FROM test_site AS dev

# Install lint, debug, etc. on top of site test as well as some helpful tools
# Modify permissions as well and make the default user root
# Even though it is reccomended to use user geoips_user
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    ssh vim wget sudo \
    && rm -rf /var/lib/apt/lists/* \
    && git config --global --add safe.directory '*' \
    && usermod -aG sudo ${USER} \
    && echo "${USER} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers \
    && chown -R geoips_user /output/ \
    && chmod -R 0777 /output/ \
    && chown -R geoips_user /packages/ \
    && chmod -R 0777 /packages/
RUN python -m pip install --no-cache-dir -e "$GEOIPS_PACKAGES_DIR/geoips/[doc,test,lint,debug]"

###############################################################################
#                              PRODUCTION STAGE
###############################################################################
FROM build AS production

USER root

# I'm not sure if this actually achieves the goal...
# Remove unnecessary files for smaller production image
RUN cd "$GEOIPS_PACKAGES_DIR/geoips" \
    && rm -rf \
       CHANGELOG_TEMPLATE.rst \
       environments \
       .github \
       pyproject.toml \
       tests \
       CODE_OF_CONDUCT.md \
       Dockerfile \
       .flake8 \
       .gitignore \
       pytest.ini \
       update_this_release_note \
       bandit.yml \
       COMMIT_MESSAGE_TEMPLATE.md \
       .dockerignore \
       interface_notes.md \
       README.md \
       CHANGELOG.rst \
       .config \
       docs \
       setup \
       requirements.txt \
    && apt-get remove -y \
       git \
       make \
       g++ \
       wget \
       gfortran \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Switch back to non-root for runtime
USER ${USER}
WORKDIR ${GEOIPS_PACKAGES_DIR}/geoips

# By default, provide a simple help CMD and a direct ENTRYPOINT
ENTRYPOINT ["geoips"]
CMD ["geoips", "--help"]
