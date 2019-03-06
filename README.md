# NES
NES is Neural Elastic Search, a highly scalable text search system based on deep neural network.

## Run in Docker

### You are working on non-master branch 
After commit your code, do 
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