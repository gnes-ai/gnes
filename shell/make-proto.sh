#!/usr/bin/env bash

set -e

SRC_NAME=gnes.proto
SRC_DIR=../gnes/proto/
VER_FILE=../gnes/__init__.py

# generating test proto

#SRC_NAME=dummy.proto
#SRC_DIR=../tests/proto/

PLUGIN_PATH=/Volumes/TOSHIBA-4T/Documents/grpc/bins/opt/grpc_python_plugin
#PLUGIN_PATH=/user/local/grpc/bins/opt/grpc_python_plugin

printf "\e[1;33mgenerating protobuf and grpc python interface\e[0m\n"

protoc -I ${SRC_DIR} --python_out=${SRC_DIR} --grpc_python_out=${SRC_DIR} --plugin=protoc-gen-grpc_python=${PLUGIN_PATH} ${SRC_DIR}${SRC_NAME}

printf "\e[1;33mfixing grpc import\e[0m\n"
# fix import bug in google generator
sed -i '' -e '4s/.*/from\ \.\ import\ gnes_pb2\ as\ gnes__pb2/' ${SRC_DIR}gnes_pb2_grpc.py

# update protobuf version in gnes/__init__.py

OLDVER=$(sed -n 's/^__proto_version__ = '\''\(.*\)'\''$/\1/p' $VER_FILE)
printf "current proto version:\t\e[1;33m$OLDVER\e[0m\n"

NEWVER=$(echo $OLDVER | awk -F. -v OFS=. 'NF==1{print ++$NF}; NF>1{$NF=sprintf("%0*d", length($NF), ($NF+1)); print}')
printf "bump proto version to:\t\e[1;32m$NEWVER\e[0m\n"

sed -i '' -e 's/^__proto_version__ = '\''\(.*\)'\''/__proto_version__ = '\'"$NEWVER"\''/' $VER_FILE
printf "\e[1;32mAll done!\e[0m\n"