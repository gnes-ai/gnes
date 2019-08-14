#!/usr/bin/env bash

set -e

function tag_push {
    docker tag $1 $2 && docker push $2
    IMAGE_SIZE=$(docker images $1 --format "{{.Size}}")
    export MSG_CONTENT="Size: ${IMAGE_SIZE}. You can now use \`docker pull $2\` to download this image."
    export MSG_TITLE="📦 $2 is released!"
    export MSG_LINK="https://github.com/gnes-ai/gnes"

    ./shell/push-wechatwork.sh
}

function login_push {
    # login to tcloud and push to there
    docker login -u $1 -p $2 $3
    tag_push ${IMAGE_TAG} "$4/${IMAGE_TAG}"

    if [[ -z "${IS_RELEASE}" ]]; then
        printf 'done!\n'
    else
        tag_push ${IMAGE_TAG} "$4/${PROJ_NAME}:stable-${OS_TAG}"
    fi
}

PROJ_NAME=gnes
TARGET=base

if [[ -z "${IS_RELEASE}" ]]; then
    VER_TAG="latest"
else
    VER_TAG=$(git tag -l | sort -V |tail -n1)
fi


for OS_TAG in buster alpine full ubuntu18 ;
do
    IMAGE_TAG="${PROJ_NAME}:${VER_TAG}-${OS_TAG}"
    DOCKER_FILE="Dockerfiles/${OS_TAG}.Dockerfile"

    printf "i will build $IMAGE_TAG based on $DOCKER_FILE\n"

    docker build --network host --build-arg BUILD_DATE=`date -u +"%Y-%m-%dT%H:%M:%SZ"` \
                 --build-arg VCS_REF=`git rev-parse --short HEAD` \
                 --rm --target $TARGET -t $IMAGE_TAG -f $DOCKER_FILE .


    if [[ -z "${HUB_USER}" ]]; then
        printf "\$HUB_USER not set, exit"
        exit 1
    else
        login_push ${HUB_USER} ${HUB_PWD} " " gnes
    fi

    if [[ -z "${TCLOUD_USER}" ]]; then
        printf "\$TCLOUD_USER not set, exit"
        exit 1
    else
        login_push ${TCLOUD_USER} ${TCLOUD_PWD} ccr.ccs.tencentyun.com ccr.ccs.tencentyun.com/gnes
    fi
done


if [[ -z "${BADGE_WEBHOOK}" ]]; then
    printf "\$BADGE_WEBHOOK not set"
else
    curl -X POST -H 'Content-type: application/json' --data '{}' ${BADGE_WEBHOOK}
    printf "informed minibadger to update docker information"
fi


