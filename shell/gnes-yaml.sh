#!/usr/bin/env bash

set -e

function print_help() {
    printf "
    GNES YAML config generator for docker-stack/swarm/compose

    usage: gnes-yaml.sh -e=./docker-compose/.env -s=./docker-compose/basic/train-compose.yml -t=./pretrained_gnes/train-compose.yml

    \e[0;33m-e|--env\e[0m                   path for the '.env' file
    \e[0;33m-s|--source\e[0m                path for the source yaml file
    \e[0;33m-t|--target\e[0m                path for the output yaml file\n"
}

for i in "$@"; do
case $i in
    -e=*|--env=*)
    ENV_PATH="${i#*=}"
    ;;
    -s=*|--source=*)
    SOURCE_PATH="${i#*=}"
    ;;
    -t=*|--target=*)
    TARGET_PATH="${i#*=}"
    ;;
    *)
        print_help
        exit
    ;;
esac
done

function check_arg() {
    if [[ -z "$ENV_PATH" ]]; then
      printf "\e[0;31mmissing argument: -e|--env\e[0m\n"
      print_help;exit
    fi
    if [[ -z "$SOURCE_PATH" ]]; then
      printf "\e[0;31mmissing argument: -s|--source\e[0m\n"
      print_help;exit
    fi
    if [[ -z "$TARGET_PATH" ]]; then
      printf "\e[0;31mmissing argument: -t|--target\e[0m\n"
      print_help;exit
    fi
}

function make_yaml() {
    INCOME_PROXY_IN=$RANDOM
    INCOME_PROXY_OUT=$RANDOM
    MIDDLEMAN_PROXY_IN=$RANDOM
    MIDDLEMAN_PROXY_OUT=$RANDOM
    OUTGOING_PROXY_IN=$RANDOM
    OUTGOING_PROXY_OUT=$RANDOM
    (. ${ENV_PATH} && eval "echo \"$(cat ${SOURCE_PATH})\"") > ${TARGET_PATH}
    (. ${ENV_PATH} && printf "
    a yaml file is generated to ${TARGET_PATH}
    to deploy it:
    \e[0;32mdocker stack deploy --with-registry-auth --compose-file ${TARGET_PATH} my-gnes-${RANDOM}\e[0m\n")
}

check_arg
make_yaml

