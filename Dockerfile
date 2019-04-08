FROM docker.oa.com:8080/public/ailab-py3-torch:latest AS base

RUN wget https://storage.googleapis.com/bert_models/2018_11_03/chinese_L-12_H-768_A-12.zip -qO temp.zip; unzip temp.zip; rm temp.zip

RUN wget https://models-1252847528.cos.ap-guangzhou.myqcloud.com/zhs.model.tar.bz2 -qO zhs.model.tar.bz2; tar -xvjf zhs.model.tar.bz2; rm zhs.model.tar.bz2

WORKDIR /nes/

ADD . ./
RUN pip install -U -e . --process-dependency-links

FROM base AS encoder

ENTRYPOINT ["gnes", "encode"]

FROM base AS indexer

ENTRYPOINT ["gnes", "index"]