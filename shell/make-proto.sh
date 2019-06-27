#!/usr/bin/env bash

SRC_DIR=../gnes/proto/
PLUGIN_PATH=/Volumes/TOSHIBA-4T/Documents/grpc/bins/opt/grpc_python_plugin
#PLUGIN_PATH=/Users/yanlarry/Desktop/git/grpc/bins/opt/grpc_python_plugin

protoc -I ${SRC_DIR} --python_out=${SRC_DIR} --grpc_python_out=${SRC_DIR} --plugin=protoc-gen-grpc_python=${PLUGIN_PATH} ${SRC_DIR}gnes.proto

# fix import bug in google generator
sed -i '' -e '4s/.*/from\ \.\ import\ gnes_pb2\ as\ gnes__pb2/' ${SRC_DIR}gnes_pb2_grpc.py