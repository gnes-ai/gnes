#!/usr/bin/env bash

set -e

GIT_TAG=$(git rev-parse --short HEAD)
PROJ_NAME=aipd-nes

printf "your current git commit tag: \e[1;33m$GIT_TAG\e[0m\n"

docker build --rm -t docker.oa.com/public/$PROJ_NAME:$GIT_TAG .
docker push docker.oa.com/public/$PROJ_NAME:$GIT_TAG

echo 'done! and to run the container simply do:'
printf "\e[1;33mdocker run --network=host -it docker.oa.com/public/$PROJ_NAME:$GIT_TAG bash\e[0m\n"