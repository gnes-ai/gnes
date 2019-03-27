import argparse

import pkg_resources

from .. import __version__


def get_base_parser():
    # create the top-level parser
    parser = argparse.ArgumentParser(
        description='GNES v%s: Generic Neural Elastic Search '
                    'is an end-to-end solution for semantic text search' % __version__)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('--verbose', action='store_true', default=False,
                        help='turn on detailed logging for debug')
    return parser


def set_nes_index_parser(parser=get_base_parser()):
    parser.add_argument('--document', type=str, required=True,
                        help='text document(s) to index, each line is a doc')
    parser.add_argument('--yaml_path', type=argparse.FileType('r'),
                        default=pkg_resources.resource_stream('gnes',
                                                              '/'.join(
                                                                  ('resources', 'config', 'gnes', 'default.yml'))),
                        help='YAML file for the model config')
    return parser


def set_nes_search_parser(parser=get_base_parser()):
    parser.add_argument('--model_path', type=str, required=True,
                        help='binary dump of a trained encoder')
    parser.add_argument('--query', type=str, required=False,
                        help='text query(s) to search, each line is a query')
    parser.add_argument('-it', '--interactive', action='store_true', default=False,
                        help='enter the interactive mode for prompt input')
    return parser


def set_service_parser(parser=get_base_parser()):
    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help='the ip address of the host')
    parser.add_argument('--port_in', type=int, default=5555,
                        help='port for input data')
    parser.add_argument('--port_out', type=int, default=5556,
                        help='port for output data')
    parser.add_argument('--port_ctrl', type=int, default=5557,
                        help='port for control the service')
    return parser


def set_encoder_service_parser(parser=set_service_parser()):
    parser.add_argument('--model_path', type=str, default=None,
                        help='binary dump of a trained encoder')
    parser.add_argument('--train', action='store_true', default=False,
                        help='train an encoder and dump the model to a file')
    parser.add_argument('--yaml_path', type=str,
                        default=pkg_resources.resource_filename('gnes',
                                                                '/'.join(
                                                                    ('resources', 'config', 'encoder', 'default.yml'))),
                        help='binary dump of a trained encoder')
    return parser


def get_main_parser():
    # create the top-level parser
    parser = get_base_parser()
    sp = parser.add_subparsers(title='please specify a supported command',
                               description='Commands',
                               help='Description', dest='cli')

    set_nes_index_parser(sp.add_parser('index', help='building an index'))
    set_nes_search_parser(sp.add_parser('search', help='searching an index'))
    set_encoder_service_parser(sp.add_parser('encode', help='searching an index'))
    return parser
