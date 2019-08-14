#!/usr/bin/env bash

set -e

export PROJ_NAME=gnes

_docker_push() {
    TARGET="base"
    GIT_TAG=$(git rev-parse --short HEAD)
    printf "your current git commit tag: \e[1;33m$GIT_TAG\e[0m\n"
    IMAGE_FULL_TAG="${DOCKER_NAMESPACE}${PROJ_NAME}:${GIT_TAG}-${OS_TAG}"
    printf "image you are building is named as \e[1;33m$IMAGE_FULL_TAG\e[0m\n"
    docker build --rm --target $TARGET -t $IMAGE_FULL_TAG -f $DOCKER_FILE .
    IMAGE_SIZE=$(docker images ${IMAGE_FULL_TAG} --format "{{.Size}}")
    printf "your image size is \e[1;33m$IMAGE_SIZE\e[0m\n"

    if [ -z "$DOCKER_NAMESPACE" ]
    then
          printf "\e[1;33m\$DOCKER_NAMESPACE is empty, pushing is ignored\e[0m\n"
    else
        docker push ${IMAGE_FULL_TAG}
        printf 'done! and to run the container simply do:\n'
        printf "\e[1;33mdocker run --entrypoint "/bin/bash" --rm -v /data/ext_models/ext_models:/ext_data -it $IMAGE_FULL_TAG\e[0m\n"
    fi
}

_select_dockerfile() {
    PS3='Please select the Dockerfile you want to build (type 1, 2, 3, ...): '
    options=("full(~7.2GB)" "alpine(~300MB)" "buster(~800MB)" "ubuntu(~650MB)")
    select opt in "${options[@]}"
    do
        case $opt in
            "full(~7.2GB)")
                export DOCKER_FILE='Dockerfiles/full.Dockerfile'
                export OS_TAG='full'
                break
                ;;
            "alpine(~300MB)")
                export DOCKER_FILE='Dockerfiles/alpine.Dockerfile'
                export OS_TAG='alpine'
                break
                ;;
            "buster(~800MB)")
                export DOCKER_FILE='Dockerfiles/buster.Dockerfile'
                export OS_TAG='buster'
                break
                ;;
            "ubuntu(~650MB)")
                export DOCKER_FILE='Dockerfiles/ubuntu.Dockerfile'
                export OS_TAG='ubuntu'
                break
                ;;
            *) printf "invalid option $REPLY";;
        esac
    done
    printf "will build using: \e[1;33m$DOCKER_FILE\e[0m\n"
}

_select_namespace() {
    PS3='Please select the namespace you want to push (type 1 or 2): '
    options=("docker.oa" "Tencent Cloud" "do not upload")
    select opt in "${options[@]}"
    do
        case $opt in
            "docker.oa")
                export DOCKER_NAMESPACE='docker.oa.com/public/'
                break
                ;;
            "Tencent Cloud")
                export DOCKER_NAMESPACE='ccr.ccs.tencentyun.com/gnes/'
                break
                ;;
            "do not upload")
                export DOCKER_NAMESPACE=''
                break
                ;;
            *) printf "invalid option $REPLY";;
        esac
    done
    printf "your image is pushing to: \e[1;33m$DOCKER_NAMESPACE\e[0m\n"
}

if [ -z "$1" ]
then
    _select_dockerfile
    _select_namespace
    _docker_push
else
    TARGET="base"
    GIT_TAG="master"
    printf "you are publishing a new version: \e[1;33m$GIT_TAG\e[0m\n"
    docker build --target $TARGET --build-arg HTTP_PROXY=${HTTP_PROXY} --build-arg HTTPS_PROXY=${HTTPS_PROXY} --build-arg NO_PROXY=${NO_PROXY} --build-arg http_proxy=${http_proxy} --build-arg https_proxy=${https_proxy} --build-arg no_proxy=${no_proxy} --network=host --rm -t ${DOCKER_NAMESPACE}/${PROJ_NAME}:${GIT_TAG} .
    docker push ${DOCKER_NAMESPACE}/${PROJ_NAME}:${GIT_TAG}
fi