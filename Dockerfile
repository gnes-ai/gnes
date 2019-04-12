FROM docker.oa.com:8080/public/ailab-py3-torch:latest AS base

WORKDIR /nes/

ADD . ./
RUN pip install .

FROM base AS encoder

ENTRYPOINT ["gnes", "encode"]

FROM base AS indexer

ENTRYPOINT ["gnes", "index"]

FROM base AS proxy

ENTRYPOINT ["gnes", "proxy"]