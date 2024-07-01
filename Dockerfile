FROM python:3.10-slim-bullseye as base

RUN apt-get update && apt-get -y upgrade \
    && apt-get install -y wget git libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -U pip

FROM base AS doclinttest

ARG GEOIPS_OUTDIRS=/output
ENV GEOIPS_OUTDIRS=${GEOIPS_OUTDIRS}

COPY --chown=root:root . .

RUN apt-get update \
    && apt-get -y upgrade \
    && apt-get install -y texlive-full \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir .[doc,lint,test] \
    && create_plugin_registries
