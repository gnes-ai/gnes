#!/usr/bin/env bash

export BUILD_ID=$1
export SERVER_MODE="ADD"

docker pull docker.oa.com/public/aipd-gnes-encoder:$BUILD_ID
docker pull docker.oa.com/public/aipd-gnes-indexer:$BUILD_ID
docker-compose up