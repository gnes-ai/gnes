"""Runs protoc with the gRPC plugin to generate messages and gRPC stubs."""

from grpc_tools import protoc

protoc.main((
    '',
    '-I=/usr/local/include',
    '-I=gnes/proto',
    '--python_out=gnes/proto',
    '--grpc_python_out=gnes/proto',
    'gnes/proto/gnes.proto',
))