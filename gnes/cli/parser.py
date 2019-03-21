import argparse
import sys

import pkg_resources
from termcolor import colored

from .. import __version__


def get_args_parser():
    # create the top-level parser
    parser = argparse.ArgumentParser(
        description='GNES v%s: Generic Neural Elastic Search '
                    'is an end-to-end solution for semantic text search' % __version__)
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s ' + __version__)
    subparsers = parser.add_subparsers(title='please specify a supported command',
                                       description='Commands',
                                       help='Description')

    # create the parser for the "command_a" command
    parser_a = subparsers.add_parser('index', help='indexing document')
    parser_a.add_argument('-d', '--document', type=str, required=True,
                          help='text document(s) to index, each line is a doc')
    parser_a.add_argument('-c', '--config', type=argparse.FileType('r'),
                          default=pkg_resources.resource_stream('gnes',
                                                                '/'.join(('resources', 'config', 'default.yml'))),
                          help='YAML file for the model config')

    # create the parser for the "command_b" command
    parser_b = subparsers.add_parser('query', help='querying an index')
    parser_b.add_argument('-c', '--config', type=str, required=True,
                          help='YAML file for the model config')
    parser_b.add_argument('-q', '--query', type=str, required=True,
                          help='text query(s) to search, each line is a query')

    return parser


def get_run_args(parser_fn=get_args_parser, printed=True):
    parser = parser_fn()
    if len(sys.argv) > 1:
        args = parser.parse_args()
        if printed:
            param_str = '\n'.join(['%20s = %s' % (colored(k, 'yellow'), v) for k, v in sorted(vars(args).items())])
            print('usage: %s\n%s\n%s\n' % (' '.join(sys.argv), '_' * 50, param_str))
        return args
    else:
        parser.print_help()
        exit()
