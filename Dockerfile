FROM docker.oa.com:8080/public/ailab-faiss:latest

RUN echo $HTTP_PROXY
RUN echo $HTTPS_PROXY
RUN echo $NO_PROXY
RUN echo $http_proxy
RUN echo $https_proxy
RUN echo $no_proxy

RUN wget https://storage.googleapis.com/bert_models/2018_11_03/chinese_L-12_H-768_A-12.zip -O temp.zip; unzip temp.zip; rm temp.zip

WORKDIR /nes/

ADD requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ADD . ./

