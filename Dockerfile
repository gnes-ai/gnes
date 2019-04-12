FROM docker.oa.com:8080/public/ailab-py3-torch:latest AS base

ADD download_model.sh ./
RUN chmod +x download_model.sh; ./download_model.sh

WORKDIR /nes/

ADD . ./
RUN pip install -U -e .

FROM base AS encoder

ENTRYPOINT ["gnes", "encode"]

FROM base AS indexer

ENTRYPOINT ["gnes", "index"]