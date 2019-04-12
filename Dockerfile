FROM docker.oa.com:8080/public/ailab-py3-torch:latest AS base

WORKDIR /nes/

ADD . ./
RUN pip install -U -e .

FROM base AS encoder

ENTRYPOINT ["gnes", "encode"]

FROM base AS indexer

ENTRYPOINT ["gnes", "index"]