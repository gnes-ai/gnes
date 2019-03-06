#!/usr/bin/env bash

GIT_TAG=$(git rev-parse --short HEAD)

echo -e "your current git commit tag: \e[1;33m$GIT_TAG\e[0m"

docker build --rm -t docker.oa.com/public/nes:$GIT_TAG .
docker push docker.oa.com/public/nes:$GIT_TAG

echo 'done! and to run the container simply do:'
echo -e "\e[1;33mdocker run --network=host -it docker.oa.com/public/nes:$GIT_TAG bash\e[0m"