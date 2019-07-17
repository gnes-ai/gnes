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

# pylint: disable=low-comment-ratio


import argparse

IDX_PORT_DELTA = 2


def set_base_parser():
    from .. import __version__
    # create the top-level parser
    parser = argparse.ArgumentParser(
        description='GNES v%s: Generic Neural Elastic Search '
                    'is an end-to-end solution for semantic text search' % __version__)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('--verbose', action='store_true', default=False,
                        help='turn on detailed logging for debug')
    return parser


def set_composer_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    parser.add_argument('--port',
                        type=int,
                        default=8800,
                        help='host port of the grpc service')
    parser.add_argument('--name',
                        type=str,
                        default='GNES instance',
                        help='name of the instance')
    parser.add_argument('--yaml_path', type=argparse.FileType('r'),
                        required=True,
                        help='yaml config of the service')
    parser.add_argument('--html_path', type=argparse.FileType('w', encoding='utf8'),
                        default='./gnes-board.html',
                        help='output path of the HTML file, will contain all possible generations')
    parser.add_argument('--shell_path', type=argparse.FileType('w', encoding='utf8'),
                        help='output path of the shell-based starting script')
    parser.add_argument('--swarm_path', type=argparse.FileType('w', encoding='utf8'),
                        help='output path of the docker-compose file for Docker Swarm')
    parser.add_argument('--k8s_path', type=argparse.FileType('w', encoding='utf8'),
                        help='output path of the docker-compose file for Docker Swarm')
    parser.add_argument('--shell_log_redirect', type=str,
                        help='the file path for redirecting shell output. '
                             'when not given, the output will be flushed to stdout')
    parser.add_argument('--mermaid_leftright', action='store_true', default=False,
                        help='showing the flow in left-to-right manner rather than top down')
    parser.add_argument('--docker_img', type=str,
                        default='gnes/gnes:latest',
                        help='the docker image used in Docker Swarm & Kubernetes')
    return parser


def set_service_parser(parser=None):
    from ..service.base import SocketType, BaseService
    if not parser:
        parser = set_base_parser()
    parser.add_argument('--port_in', type=int, default=5310,
                        help='port for input data')
    parser.add_argument('--port_out', type=int, default=5311,
                        help='port for output data')
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
    parser.add_argument('--port_ctrl', type=int, default=None,
                        help='port for control the service')
    parser.add_argument('--timeout', type=int, default=-1,
                        help='timeout (ms) of all communication, -1 for waiting forever')
    parser.add_argument('--dump_interval', type=int, default=5,
                        help='dump the service every n seconds')
    parser.add_argument('--read_only', action='store_true', default=False,
                        help='do not allow the service to modify the model, '
                             'dump_path and dump_interval will be ignored')
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
    import pkg_resources
    from ..service.base import SocketType
    set_service_parser(parser)

    parser.add_argument('--dump_path', type=str, default=None,
                        help='binary dump of the service')
    parser.add_argument('--yaml_path', type=argparse.FileType('r'),
                        default=pkg_resources.resource_stream(
                            'gnes', '/'.join(('resources', 'config', 'encoder', 'default.yml'))),
                        help='yaml config of the service')

    parser.set_defaults(socket_in=SocketType.PULL_BIND,
                        socket_out=SocketType.PUSH_BIND)
    return parser


def set_preprocessor_service_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    import pkg_resources
    set_loadable_service_parser(parser)
    parser.set_defaults(yaml_path=pkg_resources.resource_stream(
        'gnes', '/'.join(('resources', 'config', 'preprocessor', 'default.yml'))))

    parser.set_defaults(read_only=True)
    return parser


def set_router_service_parser(parser=None):
    import pkg_resources
    if not parser:
        parser = set_base_parser()
    set_loadable_service_parser(parser)
    parser.set_defaults(yaml_path=pkg_resources.resource_stream(
        'gnes', '/'.join(('resources', 'config', 'router', 'default.yml'))))

    parser.set_defaults(read_only=True)
    return parser


def set_indexer_service_parser(parser=None):
    from ..service.base import SocketType
    import pkg_resources

    if not parser:
        parser = set_base_parser()
    set_loadable_service_parser(parser)
    parser.set_defaults(yaml_path=pkg_resources.resource_stream(
        'gnes', '/'.join(('resources', 'config', 'indexer', 'default.yml'))))

    # encoder's port_out is indexer's port_in
    parser.set_defaults(port_in=parser.get_default('port_out'),
                        port_out=parser.get_default('port_out') + IDX_PORT_DELTA,
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
    return parser


def set_grpc_frontend_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    _set_client_parser(parser)
    _set_grpc_parser(parser)
    parser.add_argument('--max_concurrency', type=int, default=10,
                        help='maximum concurrent client allowed')
    parser.add_argument('--max_send_size', type=int, default=100,
                        help='maximum send size for grpc server in (MB)')
    parser.add_argument('--max_receive_size', type=int, default=100,
                        help='maximum receive size for grpc server in (MB)')
    return parser


def set_cli_client_parser(parser=None):
    import sys
    if not parser:
        parser = set_base_parser()
    _set_grpc_parser(parser)
    parser.add_argument('--txt_file', type=argparse.FileType('r'),
                        default=sys.stdin,
                        help='text file to be used, each line is a doc/query')
    parser.add_argument('--batch_size', type=int, default=100,
                        help='the size of the request to split')
    parser.add_argument('--mode', choices=['index', 'query', 'train'], type=str,
                        required=True,
                        help='the mode of the client and the server')
    parser.add_argument('--data_type', choices=['text', 'image', 'video'], type=str,
                        required=True,
                        help='type of data, available choice: text, image, video')
    parser.add_argument('--image_zip_file', type=str,
                        help='image zip file to be used, consists of multiple images')
    parser.add_argument('--top_k', type=int,
                        default=10,
                        help='default top_k for query mode')
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
    sp = parser.add_subparsers(dest='cli')

    set_grpc_frontend_parser(sp.add_parser('frontend', help='start a grpc frontend service'))
    set_indexer_service_parser(sp.add_parser('index', help='start an indexer service'))
    set_loadable_service_parser(sp.add_parser('encode', help='start an encoder service'))
    set_router_service_parser(sp.add_parser('route', help='start a router service'))
    set_preprocessor_service_parser(sp.add_parser('preprocess', help='start a preprocessor service'))
    set_http_service_parser(sp.add_parser('client_http', help='start a http service'))
    set_cli_client_parser(sp.add_parser('client_cli', help='start a grpc client'))
    set_composer_parser(sp.add_parser('compose', help='start a GNES composer to simplify config generation'))
    return parser
