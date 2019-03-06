FROM ailab-faiss:latest

RUN wget https://storage.googleapis.com/bert_models/2018_11_03/chinese_L-12_H-768_A-12.zip -O temp.zip; unzip temp.zip; rm temp.zip

WORKDIR /nes/

ADD requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ADD . ./

