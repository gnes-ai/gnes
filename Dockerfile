FROM docker.oa.com:8080/public/ailab-faiss:latest AS base

RUN apt-get install tar

RUN wget https://storage.googleapis.com/bert_models/2018_11_03/chinese_L-12_H-768_A-12.zip -qO temp.zip; unzip temp.zip; rm temp.zip

RUN wget http://pbmpb9h15.bkt.gdipper.com/zhs.model.tar.xz;
tar -xJf zhs.model.tar.xz; rm zhs.model.tar.xz

WORKDIR /nes/

ADD . ./
RUN pip install -U -e .

FROM base AS encoder

ENTRYPOINT ["gnes", "encode"]

FROM base AS indexer

ENTRYPOINT ["gnes", "index"]