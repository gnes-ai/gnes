# GNES
GNES is Generic Neural Elastic Search, a highly scalable text search system based on deep neural network.

## Run with Docker

```bash
docker run --network=host -v /data1/cips/data:/ext_data -it docker.oa.com/public/aipd-nes:master bash
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