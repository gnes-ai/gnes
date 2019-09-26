FROM ubuntu:18.04 AS base

ARG VCS_REF
ARG BUILD_DATE

LABEL maintainer="team@gnes.ai" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/gnes-ai/gnes/commit/$VCS_REF" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="GNES is Generic Nerual Elastic Search"

WORKDIR /gnes/

RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/* \
 && locale-gen "en_US.UTF-8"

ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential python3-dev python3-pip python3-setuptools libopenblas-dev && \
    export LC_ALL=en_US.UTF-8 && export LANG=en_US.UTF-8 && export LC_CTYPE=en_US.UTF-8 && \
    ln -s /usr/bin/python3 python && \
    apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

ADD setup.py MANIFEST.in requirements.txt README.md ./
ADD gnes ./gnes/

RUN pip3 install . --no-cache-dir --compile && \
    rm -rf /tmp/* && rm -rf /gnes

WORKDIR /

ENV GNES_VCS_VERSION=$VCS_REF
ENV GNES_BUILD_DATE=$BUILD_DATE

ENTRYPOINT ["gnes"]