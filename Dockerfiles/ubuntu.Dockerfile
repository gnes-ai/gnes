FROM ubuntu:18.04 AS base

WORKDIR /gnes/

RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/* \
 && locale-gen "en_US.UTF-8"

ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

ADD . ./

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential python3-dev python3-pip python3-setuptools libopenblas-dev && \
    export LC_ALL=en_US.UTF-8 && export LANG=en_US.UTF-8 && export LC_CTYPE=en_US.UTF-8 && \
    ln -s /usr/bin/python3 python && \
    pip3 install . --no-cache-dir --compile && \
    rm -rf /tmp/* && rm -rf /gnes && \
    apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /

ENTRYPOINT ["gnes"]