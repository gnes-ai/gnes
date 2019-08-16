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

    if [[ -z "${DRONE_TAG}" ]]; then
        printf 'done!\n'
    else
        tag_push ${IMAGE_TAG} "$4/${PROJ_NAME}:stable-${OS_TAG}"
    fi
}

PROJ_NAME=gnes
TARGET=base

if [[ -z "${DRONE_TAG}" ]]; then
    VER_TAG="latest"
else
    VER_TAG=${DRONE_TAG}
fi


for OS_TAG in buster alpine full ubuntu18 ;
do
    IMAGE_TAG="${PROJ_NAME}:${VER_TAG}-${OS_TAG}"
    DOCKER_FILE="Dockerfiles/${OS_TAG}.Dockerfile"

    printf "i will build $IMAGE_TAG based on $DOCKER_FILE\n"

    docker build --network host --build-arg BUILD_DATE=`date -u +"%Y-%m-%dT%H:%M:%SZ"` \
                 --build-arg VCS_REF=${DRONE_COMMIT_REF} \
                 --rm --target $TARGET -t $IMAGE_TAG -f $DOCKER_FILE .


    if [[ -z "${HUB_USER}" ]]; then
        printf "\$HUB_USER not set, pass\n"
    else
        login_push ${HUB_USER} ${HUB_PWD} " " gnes
    fi

    if [[ -z "${TCLOUD_USER}" ]]; then
        printf "\$TCLOUD_USER not set, pass\n"
    else
        login_push ${TCLOUD_USER} ${TCLOUD_PWD} ccr.ccs.tencentyun.com ccr.ccs.tencentyun.com/gnes
    fi
done

# make alpine as default
ALPINE_TAG="${PROJ_NAME}:${VER_TAG}-alpine"
DEFAULT_TAG="${PROJ_NAME}:${VER_TAG}"
docker tag ${ALPINE_TAG} ${DEFAULT_TAG} && docker push ${DEFAULT_TAG}

if [[ -z "${BADGE_WEBHOOK}" ]]; then
    printf "\$BADGE_WEBHOOK not set, pass\n"
else
    curl -X POST -H 'Content-type: application/json' --data '{}' ${BADGE_WEBHOOK}
    printf "informed minibadger to update docker information"
fi


