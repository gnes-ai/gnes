#!/usr/bin/env bash

SRC_DIR=gnes/proto/
PLUGIN_PATH=/Volumes/TOSHIBA-4T/Documents/grpc/bins/opt/grpc_python_plugin

protoc -I ${SRC_DIR} --python_out=${SRC_DIR} --grpc_python_out=${SRC_DIR} --plugin=protoc-gen-grpc_python=${PLUGIN_PATH} ${SRC_DIR}gnes.proto