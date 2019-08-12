FROM ubuntu:18.04 AS base

WORKDIR /gnes/

ADD . ./

RUN apt-get update && apt-get install --no-install-recommends -y \
            build-essential \
            python3-dev python3-pip libopenblas-dev && \
    ln -s locale.h /usr/include/xlocale.h && \
    cd /usr/local/bin && \
    ln -s /usr/bin/python3 python && \
    pip3 install --upgrade pip && \
    pip3 install . --no-cache-dir --compile && \
    rm -rf /tmp/* && rm -rf /gnes && \
    apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/* && \
    rm /usr/include/xlocale.h

WORKDIR /

ENTRYPOINT ["gnes"]