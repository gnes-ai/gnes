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


def set_nes_index_parser(parser=None):
    import pkg_resources

    if not parser:
        parser = set_base_parser()
    parser.add_argument('--document', type=str, required=True,
                        help='text document(s) to index, each line is a doc')
    parser.add_argument('--yaml_path', type=argparse.FileType('r'),
                        default=pkg_resources.resource_stream('gnes',
                                                              '/'.join(
                                                                  ('resources', 'config', 'gnes', 'default.yml'))),
                        help='YAML file for the model config')
    return parser


def set_nes_search_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    parser.add_argument('--dump_path', type=str, required=True,
                        help='binary dump of a trained encoder')
    parser.add_argument('--query', type=str, required=False,
                        help='text query(s) to search, each line is a query')
    parser.add_argument('-it', '--interactive', action='store_true', default=False,
                        help='enter the interactive mode for prompt input')
    return parser


def set_service_parser(parser=None):
    from ..service.base import SocketType, BaseService
    from ..messaging import MessageType
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
    parser.add_argument('--unk_msg_route', type=str, default=MessageType.DEFAULT.name,
                        help='handler route for unknown message type')
    parser.add_argument('--timeout', type=int, default=5000,
                        help='timeout (ms) of all communication')
    parser.add_argument('--dump_interval', type=int, default=5,
                        help='dump the service every n seconds')
    parser.add_argument('--read_only', action='store_true', default=False,
                        help='do not allow the service to modify the model, '
                             'dump_path and dump_interval will be ignored')
    return parser


def set_client_parser(parser=None):
    from ..service.base import SocketType
    if not parser:
        parser = set_base_parser()
    set_service_parser(parser)
    import sys
    import uuid
    parser.add_argument('--identity', type=str, default=str(uuid.uuid4()),
                        help='unique id string of this client')
    parser.add_argument('--wait_reply', action='store_true', default=False,
                        help='mode of this client')
    parser.add_argument('--txt_file', type=argparse.FileType('r'),
                        default=sys.stdin,
                        help='text file to be used, each line is a doc/query')
    parser.add_argument('--index', action='store_true', default=False,
                        help='merge result from multiple indexer')
    parser.add_argument('--train', action='store_true', default=False,
                        help='training in index')
    parser.set_defaults(
        port_in=parser.get_default('port_out') + IDX_PORT_DELTA,
        port_out=parser.get_default('port_in'),
        socket_in=SocketType.SUB_CONNECT,
        socket_out=SocketType.PUSH_CONNECT)
    return parser


def set_encoder_service_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    import pkg_resources
    from ..service.base import ServiceMode, SocketType
    set_service_parser(parser)
    parser.add_argument('--dump_path', type=str, default=None,
                        help='binary dump of the service')
    parser.add_argument('--mode', type=ServiceMode.from_string, choices=list(ServiceMode),
                        required=True,
                        help='mode of this service')
    parser.add_argument('--yaml_path', type=argparse.FileType('r'),
                        default=pkg_resources.resource_stream(
                            'gnes', '/'.join(('resources', 'config', 'encoder', 'default.yml'))),
                        help='yaml config of the service')

    parser.set_defaults(socket_in=SocketType.PULL_BIND,
                        socket_out=SocketType.PUSH_BIND)
    return parser


def set_proxy_service_parser(parser=None):
    from ..service.base import SocketType
    from inspect import isclass
    from ..service import proxy as my_proxy
    if not parser:
        parser = set_base_parser()
    set_service_parser(parser)
    parser.add_argument('--proxy_type', type=str, default='ProxyService',
                        choices=[x for x in dir(my_proxy) if isclass(getattr(my_proxy, x))],
                        help='type of proxy')
    parser.add_argument('--batch_size', type=int, default=None,
                        help='the size of the request to split')
    parser.add_argument('--num_part', type=int, default=1,
                        help='the number of partial result to collect')
    parser.set_defaults(socket_in=SocketType.PULL_BIND,
                        socket_out=SocketType.PUB_BIND)
    return parser


def set_indexer_service_parser(parser=None):
    from ..service.base import SocketType
    import pkg_resources

    if not parser:
        parser = set_base_parser()
    set_encoder_service_parser(parser)
    parser.add_argument('--top_k', type=int, default=10,
                        help='number of top results to retrieve')
    parser.set_defaults(yaml_path=pkg_resources.resource_stream(
        'gnes', '/'.join(('resources', 'config', 'indexer', 'default.yml'))))

    # encoder's port_out is indexer's port_in
    parser.set_defaults(port_in=parser.get_default('port_out'),
                        port_out=parser.get_default('port_out') + IDX_PORT_DELTA,
                        socket_in=SocketType.PULL_CONNECT,
                        socket_out=SocketType.PUB_BIND)
    return parser

def set_grpc_service_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    set_service_parser(parser)
    parser.add_argument('--num_procs',
                        type=int,
                        default=1,
                        help="the number of process to use for serving")
    parser.add_argument("--grpc_host",
                        type=str,
                        default="0.0.0.0",
                        help="host address for grpc service")
    parser.add_argument("--grpc_port",
                        type=str,
                        default="5555",
                        help="host port for grpc service")

    return parser


def set_grpc_client_parser(parser=None):
    import sys
    if not parser:
        parser = set_base_parser()
    set_service_parser(parser)

    parser.add_argument('--grpc_host', type=str, default='127.0.0.1',
                        help='the grpc host name')
    parser.add_argument('--grpc_port', type=str, default="8800",
                        help='the grpc port')
    parser.add_argument('--txt_file', type=argparse.FileType('r'),
                        default=sys.stdin,
                        help='text file to be used, each line is a doc/query')
    parser.add_argument('--batch_size', type=int, default=None,
                        help='the size of the request to split')
    parser.add_argument('--query', action='store_true', default=False,
                        help='merge result from multiple indexer')
    parser.add_argument('--index', action='store_true', default=False,
                        help='merge result from multiple indexer')
    parser.add_argument('--train', action='store_true', default=False,
                        help='training in index')

    return parser



def get_main_parser():
    # create the top-level parser
    parser = set_base_parser()
    sp = parser.add_subparsers(title='please specify a supported command',
                               description='Commands',
                               help='Description', dest='cli')

    set_client_parser(sp.add_parser('client', help='start a client'))
    set_grpc_client_parser(sp.add_parser('grpc_client', help="start a grpc client"))
    set_grpc_service_parser(sp.add_parser('grpc_serve', help="start a grpc service"))
    set_indexer_service_parser(sp.add_parser('index', help='start an indexer service'))
    set_encoder_service_parser(sp.add_parser('encode', help='start an encoder service'))
    set_proxy_service_parser(sp.add_parser('proxy', help='start a proxy service'))
    return parser
