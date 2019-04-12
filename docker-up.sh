#!/usr/bin/env bash

export BUILD_ID=$1
export SERVER_MODE=$2

# export some variables for the use in docker-compose.yaml
export MUID=$UID
export OUTPUT_DIR=$(pwd)"/tmp_data"


function rand_port {
    shuf -i 2000-65000 -n 1
}

export INCOME_PROXY_IN=$(rand_port)
export INCOME_PROXY_OUT=$(rand_port)
export MIDDLEMAN_PROXY_IN=$(rand_port)
export MIDDLEMAN_PROXY_OUT=$(rand_port)
export OUTGOING_PROXY_IN=$(rand_port)
export OUTGOING_PROXY_OUT=$(rand_port)

mkdir -p ${OUTPUT_DIR}
docker pull docker.oa.com/public/aipd-gnes-encoder:$BUILD_ID
docker pull docker.oa.com/public/aipd-gnes-indexer:$BUILD_ID
docker-compose up

# shutdown docker-compose
docker-compose down