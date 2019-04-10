#!/usr/bin/env bash

export MUID=$UID
export BUILD_ID=$1
export SERVER_MODE=$2
export OUTPUT_DIR=$(pwd)"/tmp_data"

mkdir -p $OUTPUT_DIR
docker pull docker.oa.com/public/aipd-gnes-encoder:$BUILD_ID
docker pull docker.oa.com/public/aipd-gnes-indexer:$BUILD_ID
docker-compose up

docker-compose down