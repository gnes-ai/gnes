FROM docker.oa.com:8080/public/ailab-faiss:latest AS base

RUN wget https://storage.googleapis.com/bert_models/2018_11_03/chinese_L-12_H-768_A-12.zip -qO temp.zip; unzip temp.zip; rm temp.zip

WORKDIR /nes/

ADD . ./
RUN pip install -U -e .

FROM gnes-base AS encoder

ENTRYPOINT ["gnes", "encode"]

FROM gnes-base AS indexer

ENTRYPOINT ["gnes", "index"]