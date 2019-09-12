FROM python:3.7.4-alpine AS base

ARG VCS_REF
ARG BUILD_DATE

LABEL maintainer="team@gnes.ai" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/gnes-ai/gnes" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="GNES is Generic Nerual Elastic Search"

WORKDIR /gnes/

ADD . ./

RUN apk add --no-cache \
            --virtual=.build-dependencies \
            build-base g++ gfortran file binutils zeromq-dev \
            musl-dev python3-dev py-pgen cython openblas-dev && \
    apk add --no-cache libstdc++ openblas libzmq && \
    ln -s locale.h /usr/include/xlocale.h && \
    pip install . --no-cache-dir --compile && \
    find /usr/lib/python3.7/ -name 'tests' -exec rm -r '{}' + && \
    find /usr/lib/python3.7/site-packages/ -name '*.so' -print -exec sh -c 'file "{}" | grep -q "not stripped" && strip -s "{}"' \; && \
    rm /usr/include/xlocale.h && \
    rm -rf /tmp/* && \
    rm -rf /gnes && \
    apk del .build-dependencies && \
    rm -rf /var/cache/apk/*

WORKDIR /

ENTRYPOINT ["gnes"]