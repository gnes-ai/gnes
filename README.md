# GNES

[![build status](http://badge.orange-ci.oa.com/ai-innersource/nes.svg)]()


GNES is Generic Neural Elastic Search, a highly scalable text search system based on deep neural network.

## Install

```bash
pip install -e . -U
```

## Run with Docker

```bash
docker run -v /data1/cips/data:/ext_data -it docker.oa.com/public/aipd-gnes:master bash
```

To maintainers, after commit your code, please do 
```bash
bash docker-push.sh
```
and then follow the guidelines in yellow. 

Note that `/data1/cips/data` is mounted to `/ext_data` in the container.

## Test

To run all unit tests:

```bash
python -m unittest tests/*.py
```


To enable profiling:

```bash
export NES_PROFILING=1
```

## Run Encoder Service via Docker

```bash
docker run -v $(pwd)/test.yml:/test.yml -v /data1/cips/data:/ext_data docker.oa.com/public/aipd-gnes-encoder:5930f22 --train --yaml_path /test.yml
```
