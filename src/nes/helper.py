import argparse
import logging
import os
import sys
import time

from termcolor import colored


def set_logger(context, verbose=False):
    if os.name == 'nt':  # for Windows
        return NTLogger(context, verbose)

    logger = logging.getLogger(context)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    formatter = logging.Formatter(
        '%(levelname)-.1s:' + context + ':[%(filename).3s:%(funcName).3s:%(lineno)3d]:%(message)s', datefmt=
        '%m-%d %H:%M:%S')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_handler.setFormatter(formatter)
    logger.handlers = []
    logger.addHandler(console_handler)
    return logger


class NTLogger:
    def __init__(self, context, verbose):
        self.context = context
        self.verbose = verbose

    def info(self, msg, **kwargs):
        print('I:%s:%s' % (self.context, msg), flush=True)

    def debug(self, msg, **kwargs):
        if self.verbose:
            print('D:%s:%s' % (self.context, msg), flush=True)

    def error(self, msg, **kwargs):
        print('E:%s:%s' % (self.context, msg), flush=True)

    def warning(self, msg, **kwargs):
        print('W:%s:%s' % (self.context, msg), flush=True)


def get_args_parser():
    from . import __version__
    parser = argparse.ArgumentParser()

    group1 = parser.add_argument_group('Index options',
                                       'config index input, vector size, etc.')
    group1.add_argument('-data_file', type=argparse.FileType('rb'), required=True,
                        help='the path of the binary file to be indexed')
    group1.add_argument('-query_file', type=argparse.FileType('rb'), required=True,
                        help='the path of the binary file to be queried')
    group1.add_argument('-bytes_per_vector', type=int, required=True,
                        help='number of bytes per vector')
    group1.add_argument('-num_data', type=int, default=None,
                        help='maximum number of vector to query')
    group1.add_argument('-num_query', type=int, default=None,
                        help='maximum number of vector to index')
    group1.add_argument('-index_mode', type=str, choices=['none', 'trie'], default='trie',
                        help='indexing mode')
    group1.add_argument('-txt_file', type=str, default='train.wechat.txt',
                        help='text file name')

    parser.add_argument('-verbose', action='store_true', default=False,
                        help='turn on additional logging for debug')
    parser.add_argument('-version', action='version', version='%(prog)s ' + __version__)
    return parser


def get_run_args(parser_fn=get_args_parser, printed=True):
    args = parser_fn().parse_args()
    if printed:
        param_str = '\n'.join(['%20s = %s' % (k, v) for k, v in sorted(vars(args).items())])
        print('usage: %s\n%20s   %s\n%s\n%s\n' % (' '.join(sys.argv), 'ARG', 'VALUE', '_' * 50, param_str))
    return args


class TimeContext:
    def __init__(self, msg):
        self._msg = msg

    def __enter__(self):
        self.start = time.perf_counter()
        print(self._msg, end=' ...\t', flush=True)

    def __exit__(self, typ, value, traceback):
        self.duration = time.perf_counter() - self.start
        print(colored('    [%3.3f secs]' % self.duration, 'green'), flush=True)
