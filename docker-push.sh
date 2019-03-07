#!/usr/bin/env bash

set -e

GIT_TAG=$1
PORT=$2
PROXY=$3

if [ -z "$1" ]
  then
    GIT_TAG=$(git rev-parse --short HEAD)
fi

PROJ_NAME=aipd-nes

printf "your current git commit tag: \e[1;33m$GIT_TAG\e[0m\n"

docker build $PROXY --rm -t docker.oa.com$PORT/public/$PROJ_NAME:$GIT_TAG .
docker push docker.oa.com$PORT/public/$PROJ_NAME:$GIT_TAG

echo 'done! and to run the container simply do:'
printf "\e[1;33mdocker run --network=host -v /data1/cips/data:/ext_data -it docker.oa.com/public/$PROJ_NAME:$GIT_TAG bash\e[0m\n"