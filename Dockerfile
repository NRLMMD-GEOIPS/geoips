FROM python:3.10-slim-bullseye AS base

RUN apt-get update && apt-get -y upgrade \
    && apt-get install -y wget git libopenblas-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -U pip

FROM base AS doclinttest

WORKDIR /packages/geoips

ARG GEOIPS_OUTDIRS=/output
ENV GEOIPS_OUTDIRS=${GEOIPS_OUTDIRS}

COPY --chown=root:root . .

# RUN apt-get update \
#     && apt-get -y upgrade \
#     && apt-get install -y \
#         texlive-latex-base \
#         texlive-latex-recommended \
#         texlive-latex-extra \
#         texlive-fonts-recommended \
#         texlive-fonts-extra \
#         texlive-science \
#         texlive-xetex \
#         latexmk \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# RUN apt-get update \
#     && apt-get -y upgrade \
#     && apt-get install -y \
#         texlive-latex-base \
#         latexmk \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir .[doc,lint,test] \
    && create_plugin_registries
