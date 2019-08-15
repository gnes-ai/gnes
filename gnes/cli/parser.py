#  Tencent is pleased to support the open source community by making GNES available.
#
#  Copyright (C) 2019 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


import argparse


def resolve_yaml_path(path):
    # priority, filepath > classname > default
    import os
    import io
    if hasattr(path, 'read'):
        # already a readable stream
        return path
    elif os.path.exists(path):
        return open(path, encoding='utf8')
    elif path.isidentifier():
        # possible class name
        return io.StringIO('!%s {}' % path)
    elif path.startswith('!'):
        # possible YAML content
        return io.StringIO(path)
    else:
        raise argparse.ArgumentTypeError('%s can not be resolved, it should be a readable stream,'
                                         ' or a valid file path, or a supported class name.' % path)


def set_base_parser():
    from .. import __version__
    from termcolor import colored
    # create the top-level parser
    parser = argparse.ArgumentParser(
        description='%s, a cloud-native semantic search system '
                    'based on deep neural network. '
                    'It enables large-scale index and semantic search for text-to-text, image-to-image, '
                    'video-to-video and any content form. Visit %s for tutorials and documentations.' % (
                        colored('GNES v%s: Generic Neural Elastic Search' % __version__, 'green'),
                        colored('https://gnes.ai', 'cyan', attrs=['underline'])))
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('--verbose', action='store_true', default=False,
                        help='turn on detailed logging for debug')
    return parser


def set_composer_parser(parser=None):
    from pkg_resources import resource_stream

    if not parser:
        parser = set_base_parser()
    parser.add_argument('--port',
                        type=int,
                        default=8800,
                        help='host port of the grpc service')
    parser.add_argument('--name',
                        type=str,
                        default='GNES app',
                        help='name of the instance')
    parser.add_argument('--yaml_path', type=resolve_yaml_path,
                        default=resource_stream(
                            'gnes', '/'.join(('resources', 'compose', 'gnes-example.yml'))),
                        help='yaml config of the service')
    parser.add_argument('--html_path', type=argparse.FileType('w', encoding='utf8'),
                        help='output path of the HTML file, will contain all possible generations')
    parser.add_argument('--shell_path', type=argparse.FileType('w', encoding='utf8'),
                        help='output path of the shell-based starting script')
    parser.add_argument('--swarm_path', type=argparse.FileType('w', encoding='utf8'),
                        help='output path of the docker-compose file for Docker Swarm')
    parser.add_argument('--k8s_path', type=argparse.FileType('w', encoding='utf8'),
                        help='output path of the docker-compose file for Docker Swarm')
    parser.add_argument('--graph_path', type=argparse.FileType('w', encoding='utf8'),
                        help='output path of the mermaid graph file')
    parser.add_argument('--shell_log_redirect', type=str,
                        help='the file path for redirecting shell output. '
                             'when not given, the output will be flushed to stdout')
    parser.add_argument('--mermaid_leftright', action='store_true', default=False,
                        help='showing the flow in left-to-right manner rather than top down')
    parser.add_argument('--docker_img', type=str,
                        default='gnes/gnes:latest-alpine',
                        help='the docker image used in Docker Swarm & Kubernetes')
    return parser


def set_composer_flask_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    set_composer_parser(parser)
    parser.add_argument('--flask', action='store_true', default=False,
                        help='using Flask to serve a composer in interactive mode, aka GNES board')
    parser.add_argument('--http_port', type=int, default=8080,
                        help='server port for receiving HTTP requests')
    return parser


def set_service_parser(parser=None):
    from ..service.base import SocketType, BaseService, ParallelType
    import random
    if not parser:
        parser = set_base_parser()
    min_port, max_port = 49152, 65536
    parser.add_argument('--port_in', type=int, default=random.randrange(min_port, max_port),
                        help='port for input data, default a random port between [49152, 65536]')
    parser.add_argument('--port_out', type=int, default=random.randrange(min_port, max_port),
                        help='port for output data, default a random port between [49152, 65536]')
    parser.add_argument('--host_in', type=str, default=BaseService.default_host,
                        help='host address for input')
    parser.add_argument('--host_out', type=str, default=BaseService.default_host,
                        help='host address for output')
    parser.add_argument('--socket_in', type=SocketType.from_string, choices=list(SocketType),
                        default=SocketType.PULL_BIND,
                        help='socket type for input port')
    parser.add_argument('--socket_out', type=SocketType.from_string, choices=list(SocketType),
                        default=SocketType.PUSH_BIND,
                        help='socket type for output port')
    parser.add_argument('--port_ctrl', type=int, default=random.randrange(min_port, max_port),
                        help='port for controlling the service, default a random port between [49152, 65536]')
    parser.add_argument('--timeout', type=int, default=-1,
                        help='timeout (ms) of all communication, -1 for waiting forever')
    parser.add_argument('--dump_interval', type=int, default=5,
                        help='serialize the service to a file every n seconds')
    parser.add_argument('--read_only', action='store_true', default=False,
                        help='do not allow the service to modify the model, '
                             'dump_interval will be ignored')
    parser.add_argument('--parallel_backend', type=str, choices=['thread', 'process'], default='thread',
                        help='parallel backend of the service')
    parser.add_argument('--num_parallel', type=int, default=1,
                        help='number of parallel services running at the same time, '
                             '`port_in` and `port_out` will be set to random, '
                             'and routers will be added automatically when necessary')
    parser.add_argument('--parallel_type', type=ParallelType.from_string, choices=list(ParallelType),
                        default=ParallelType.PUSH_NONBLOCK,
                        help='parallel type of the concurrent services')
    return parser


def _set_client_parser(parser=None):
    from ..service.base import SocketType
    if not parser:
        parser = set_base_parser()
    set_service_parser(parser)
    parser.set_defaults(
        port_in=parser.get_default('port_out'),
        port_out=parser.get_default('port_in'),
        socket_in=SocketType.PULL_CONNECT,
        socket_out=SocketType.PUSH_CONNECT,
        read_only=True)
    return parser


def set_loadable_service_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    from ..service.base import SocketType
    set_service_parser(parser)

    parser.add_argument('--yaml_path', type=resolve_yaml_path, required=True,
                        help='yaml config of the service, it should be a readable stream,'
                             ' or a valid file path, or a supported class name.')

    parser.set_defaults(socket_in=SocketType.PULL_BIND,
                        socket_out=SocketType.PUSH_BIND)
    return parser


def set_preprocessor_service_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    set_loadable_service_parser(parser)
    parser.set_defaults(read_only=True)
    return parser


def set_router_service_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    set_loadable_service_parser(parser)
    parser.add_argument('--num_part', type=int, default=None,
                        help='explicitly set the number of parts of message')
    parser.set_defaults(read_only=True)
    return parser


def set_indexer_service_parser(parser=None):
    from ..service.base import SocketType

    if not parser:
        parser = set_base_parser()
    set_loadable_service_parser(parser)

    # encoder's port_out is indexer's port_in
    parser.set_defaults(port_in=parser.get_default('port_out'),
                        port_out=parser.get_default('port_out') + 2,
                        socket_in=SocketType.PULL_CONNECT,
                        socket_out=SocketType.PUB_BIND)
    return parser


def _set_grpc_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    parser.add_argument('--grpc_host',
                        type=str,
                        default='0.0.0.0',
                        help='host address of the grpc service')
    parser.add_argument('--grpc_port',
                        type=int,
                        default=8800,
                        help='host port of the grpc service')
    parser.add_argument('--max_message_size', type=int, default=100,
                        help='maximum send and receive size for grpc server in (MB)')
    return parser


def set_grpc_service_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    set_service_parser(parser)
    _set_grpc_parser(parser)
    parser.add_argument('--pb2_path',
                        type=str,
                        required=True,
                        help='the path of the python file protocol buffer compiler')
    parser.add_argument('--pb2_grpc_path',
                        type=str,
                        required=True,
                        help='the path of the python file generated by the gRPC Python protocol compiler plugin')
    parser.add_argument('--stub_name',
                        type=str,
                        required=True,
                        help='the name of the gRPC Stub')
    parser.add_argument('--api_name',
                        type=str,
                        required=True,
                        help='the api name for calling the stub')
    return parser


def set_frontend_parser(parser=None):
    from ..service.base import SocketType
    if not parser:
        parser = set_base_parser()
    set_service_parser(parser)
    _set_grpc_parser(parser)
    parser.set_defaults(socket_in=SocketType.PULL_BIND,
                        socket_out=SocketType.PUSH_BIND,
                        read_only=True)
    parser.add_argument('--max_concurrency', type=int, default=10,
                        help='maximum concurrent client allowed')
    return parser


def set_cli_client_parser(parser=None):
    import sys
    if not parser:
        parser = set_base_parser()
    _set_grpc_parser(parser)
    group = parser.add_mutually_exclusive_group()

    group.add_argument('--txt_file', type=argparse.FileType('r'),
                       default=sys.stdin,
                       help='text file to be used, each line is a doc/query')
    group.add_argument('--image_zip_file', type=str,
                       help='image zip file to be used, consists of multiple images')
    group.add_argument('--video_zip_file', type=str,
                       help='video zip file to be used, consists of multiple videos')

    parser.add_argument('--batch_size', type=int, default=100,
                        help='the size of the request to split')
    parser.add_argument('--mode', choices=['index', 'query', 'train'], type=str,
                        required=True,
                        help='the mode of the client and the server')
    parser.add_argument('--top_k', type=int,
                        default=10,
                        help='top_k results returned in the query mode')
    parser.add_argument('--start_doc_id', type=int,
                        default=0,
                        help='the start number of doc id')
    return parser


def set_benchmark_client_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    _set_grpc_parser(parser)
    parser.add_argument('--batch_size', type=int, default=64,
                        help='the size of the request to split')
    parser.add_argument('--request_length', type=int,
                        default=1024,
                        help='binary string length of each request')
    parser.add_argument('--num_requests', type=int,
                        default=128,
                        help='number of total requests')
    return parser


def set_http_service_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    _set_grpc_parser(parser)
    parser.add_argument('--http_port', type=int, default=80,
                        help='http port to deploy the service')
    parser.add_argument('--http_host', type=str, default='0.0.0.0',
                        help='http host to deploy the service')
    parser.add_argument('--max_workers', type=int, default=100,
                        help='max workers to deal with the message')
    parser.add_argument('--top_k', type=int, default=10,
                        help='default top_k for query mode')
    parser.add_argument('--batch_size', type=int, default=2560,
                        help='batch size for feed data for train mode')
    return parser


def get_main_parser():
    # create the top-level parser
    parser = set_base_parser()
    sp = parser.add_subparsers(dest='cli', title='GNES sub-commands',
                               description='use "gnes [sub-command] --help" '
                                           'to get detailed information about each sub-command')

    # microservices
    set_frontend_parser(sp.add_parser('frontend', help='start a frontend service'))
    set_loadable_service_parser(sp.add_parser('encode', help='start an encoder service'))
    set_indexer_service_parser(sp.add_parser('index', help='start an indexer service'))
    set_router_service_parser(sp.add_parser('route', help='start a router service'))
    set_preprocessor_service_parser(sp.add_parser('preprocess', help='start a preprocessor service'))
    set_grpc_service_parser(sp.add_parser('grpc', help='start a general purpose grpc service'))

    pp = sp.add_parser('client', help='start a GNES client of the selected type')
    spp = pp.add_subparsers(dest='client', title='GNES client sub-commands',
                            description='use "gnes client [sub-command] --help" '
                                        'to get detailed information about each client sub-command')
    # clients
    set_http_service_parser(spp.add_parser('http', help='start a client that allows HTTP requests as input'))
    set_cli_client_parser(spp.add_parser('cli', help='start a client that allows stdin as input'))
    set_benchmark_client_parser(spp.add_parser('benchmark', help='start a client for benchmark and unittest'))

    # others
    set_composer_flask_parser(sp.add_parser('compose', help='start a GNES Board to visualize YAML configs'))
    return parser
