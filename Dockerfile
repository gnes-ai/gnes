FROM docker.oa.com/public/ailab-faiss:latest

WORKDIR /nes/

ADD requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ADD . ./

