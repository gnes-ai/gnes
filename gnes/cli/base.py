import argparse

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
