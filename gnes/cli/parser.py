import argparse

import pkg_resources

from .. import __version__

IDX_PORT_DELTA = 2


def set_base_parser():
    # create the top-level parser
    parser = argparse.ArgumentParser(
        description='GNES v%s: Generic Neural Elastic Search '
                    'is an end-to-end solution for semantic text search' % __version__)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('--verbose', action='store_true', default=False,
                        help='turn on detailed logging for debug')
    return parser


def set_nes_index_parser(parser=None):
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
    parser.add_argument('--port_ctrl', type=int,
                        help='port for control the service')
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
    parser.set_defaults(
        port_in=parser.get_default('port_out') + IDX_PORT_DELTA,
        port_out=parser.get_default('port_in'),
        socket_in=SocketType.SUB_CONNECT,
        socket_out=SocketType.PUSH_CONNECT)
    return parser


def set_encoder_service_parser(parser=None):
    if not parser:
        parser = set_base_parser()
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
    parser.add_argument('--proxy_type', type=str,
                        choices=[x for x in dir(my_proxy) if isclass(getattr(my_proxy, x))],
                        help='type of proxy')
    parser.add_argument('--batch_size', type=int,
                        help='the size of the request to split')
    parser.add_argument('--num_part', type=int,
                        help='the number of partial result to collect')
    parser.set_defaults(socket_in=SocketType.PULL_BIND,
                        socket_out=SocketType.PUB_BIND)
    return parser


def set_indexer_service_parser(parser=None):
    from ..service.base import SocketType
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


def get_main_parser():
    # create the top-level parser
    parser = set_base_parser()
    sp = parser.add_subparsers(title='please specify a supported command',
                               description='Commands',
                               help='Description', dest='cli')

    set_client_parser(sp.add_parser('client', help='start a client'))
    set_indexer_service_parser(sp.add_parser('index', help='start an indexer service'))
    set_encoder_service_parser(sp.add_parser('encode', help='start an encoder service'))
    set_proxy_service_parser(sp.add_parser('proxy', help='start a proxy service'))
    return parser
