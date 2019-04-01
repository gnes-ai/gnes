#!/usr/bin/env bash

set -ex

TARGET=encoder
PROJ_NAME=aipd-gnes-$TARGET
GIT_TAG=$1

if [ -z "$1" ]
  then
    GIT_TAG=$(git rev-parse --short HEAD)
    printf "your current git commit tag: \e[1;33m$GIT_TAG\e[0m\n"
    docker build --rm --target $TARGET -t docker.oa.com/public/${PROJ_NAME}:$GIT_TAG .
    docker push docker.oa.com/public/$PROJ_NAME:$GIT_TAG
    printf 'done! and to run the container simply do:\n'
    printf "\e[1;33mdocker run -v /data1/cips/data:/ext_data -it docker.oa.com/public/$PROJ_NAME:$GIT_TAG bash\e[0m\n"
  else
    GIT_TAG=$1
    printf "you are publishing a new version: \e[1;33m$GIT_TAG\e[0m\n"
    docker build --build-arg HTTP_PROXY=${HTTP_PROXY} --build-arg HTTPS_PROXY=${HTTPS_PROXY} --build-arg NO_PROXY=${NO_PROXY} --build-arg http_proxy=${http_proxy} --build-arg https_proxy=${https_proxy} --build-arg no_proxy=${no_proxy} --network=host --rm -t docker.oa.com:8080/public/$PROJ_NAME:$GIT_TAG .
    docker push docker.oa.com:8080/public/$PROJ_NAME:$GIT_TAG
fi
