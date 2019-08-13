FROM python:3.7.4-slim-buster AS base

WORKDIR /gnes/

ADD . ./

RUN apt-get update && apt-get install --no-install-recommends -y \
            build-essential \
            python3-dev libopenblas-dev && \
    ln -s locale.h /usr/include/xlocale.h && \
    pip install . --no-cache-dir --compile && \
    rm -rf /tmp/* && rm -rf /gnes && \
    apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/* && \
    rm /usr/include/xlocale.h

WORKDIR /

ENTRYPOINT ["gnes"]