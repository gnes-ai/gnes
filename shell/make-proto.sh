#!/usr/bin/env bash

SRC_NAME=gnes.proto
SRC_DIR=../gnes/proto/

# generating test proto

#SRC_NAME=dummy.proto
#SRC_DIR=../tests/proto/

PLUGIN_PATH=/Volumes/TOSHIBA-4T/Documents/grpc/bins/opt/grpc_python_plugin
#PLUGIN_PATH=/user/local/grpc/bins/opt/grpc_python_plugin

protoc -I ${SRC_DIR} --python_out=${SRC_DIR} --grpc_python_out=${SRC_DIR} --plugin=protoc-gen-grpc_python=${PLUGIN_PATH} ${SRC_DIR}${SRC_NAME}

# fix import bug in google generator
#sed -i '' -e '4s/.*/from\ \.\ import\ gnes_pb2\ as\ gnes__pb2/' ${SRC_DIR}gnes_pb2_grpc.py
