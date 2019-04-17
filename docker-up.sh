#!/usr/bin/env bash

_select_namespace() {
    PS3='Please select the namespace you want to pull (type 1 or 2): '
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
    printf "you are pulling image from: \e[1;33m$DOCKER_NAMESPACE\e[0m\n"
}

_select_namespace

PROJ_NAME="aipd-gnes"

export DOCKER_IMG_URL="${DOCKER_NAMESPACE}/${PROJ_NAME}:${1}"
export SERVER_MODE=$2
export EXT_DATA_DIR="/data/ext_models/"
export INDEXER_YAML_PATH="/data/han/indexer.yml"
export ENCODER_YAML_PATH="/data/han/encoder.yml"
export HOST_PORT_IN=5598
export HOST_PORT_OUT=5599
export OUTPUT_DIR=$(pwd)"/tmp_data"


function rand_port {
    shuf -i 2000-65000 -n 1
}

export INCOME_PROXY_IN=$(rand_port)
export INCOME_PROXY_OUT=$(rand_port)
export MIDDLEMAN_PROXY_IN=$(rand_port)
export MIDDLEMAN_PROXY_OUT=$(rand_port)
export OUTGOING_PROXY_IN=$(rand_port)
export OUTGOING_PROXY_OUT=$(rand_port)

mkdir -p ${OUTPUT_DIR}
docker pull ${DOCKER_IMG_URL}
docker-compose up

# shutdown docker-compose
docker-compose down