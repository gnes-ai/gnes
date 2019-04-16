#!/usr/bin/env bash

set -e

export PROJ_NAME=aipd-gnes

_docker_push() {
    TARGET="base"
    GIT_TAG=$(git rev-parse --short HEAD)
    printf "your current git commit tag: \e[1;33m$GIT_TAG\e[0m\n"
    docker build --rm --target $TARGET -t ${DOCKER_NAMESPACE}/${PROJ_NAME}:${GIT_TAG} .
    docker push ${DOCKER_NAMESPACE}/${PROJ_NAME}:${GIT_TAG}
    printf 'done! and to run the container simply do:\n'
    printf "\e[1;33mdocker run --rm -v /data1/cips/data:/ext_data -it $DOCKER_NAMESPACE/$PROJ_NAME:$GIT_TAG bash\e[0m\n"
}

_select_namespace() {
    PS3='Please select the namespace you want to push (type 1 or 2): '
    options=("docker.oa" "Tencent Cloud")
    select opt in "${options[@]}"
    do
        case $opt in
            "docker.oa")
                export DOCKER_NAMESPACE='docker.oa.com/public'
                break
                ;;
            "Tencent Cloud")
                export DOCKER_NAMESPACE='ccr.ccs.tencentyun.com/gnes'
                break
                ;;
            *) printf "invalid option $REPLY";;
        esac
    done
    printf "your image is pushing to: \e[1;33m$DOCKER_NAMESPACE\e[0m\n"
}

if [ -z "$1" ]
then
    _select_namespace
    _docker_push
else
    TARGET="base"
    GIT_TAG="master"
    printf "you are publishing a new version: \e[1;33m$GIT_TAG\e[0m\n"
    docker build --target $TARGET --build-arg HTTP_PROXY=${HTTP_PROXY} --build-arg HTTPS_PROXY=${HTTPS_PROXY} --build-arg NO_PROXY=${NO_PROXY} --build-arg http_proxy=${http_proxy} --build-arg https_proxy=${https_proxy} --build-arg no_proxy=${no_proxy} --network=host --rm -t ${DOCKER_NAMESPACE}/${PROJ_NAME}:${GIT_TAG} .
    docker push ${DOCKER_NAMESPACE}/${PROJ_NAME}:${GIT_TAG}
fi