FROM docker.oa.com:8080/public/ailab-faiss:latest AS base

RUN wget https://storage.googleapis.com/bert_models/2018_11_03/chinese_L-12_H-768_A-12.zip -qO temp.zip; unzip temp.zip; rm temp.zip

WORKDIR /nes/

ADD . ./
RUN pip install -U -e .

FROM base AS encoder

EXPOSE 5310
EXPOSE 5311

ENTRYPOINT ["gnes", "encode"]

FROM base AS indexer

EXPOSE 5311

ENTRYPOINT ["gnes", "index"]