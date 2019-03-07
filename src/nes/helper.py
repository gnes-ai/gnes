import argparse
import html
import inspect
import logging
import os
import re
import sys
import time
from functools import wraps
from itertools import islice
from typing import Iterator, Any

import numpy as np
from termcolor import colored


def get_perm(L, m):
    n = int(len(L) / m)
    avg = sum(L) / len(L) * m
    LR = sorted(enumerate(L), key=lambda x: -x[1])
    L = np.reshape([i[1] for i in LR], [m, n])
    R = np.reshape([i[0] for i in LR], [m, n])
    F = np.zeros([m, n])

    reranked = []
    for _ in range(n):
        ind = 0
        for i in range(m):
            if i % 2 == 0:
                start, direction = 0, 1
            else:
                start, direction = n - 1, -1
            while F[i, start] == 1:
                start += direction
            if (ind + L[i, start] < avg) or (direction == 1):
                ind += L[i, start]
                F[i, start] = 1
                reranked.append(R[i, start])
            else:
                start, direction = n - 1, -1
                while F[i, start] == 1:
                    start += direction
                ind += L[i, start]
                F[i, start] = 1
                reranked.append(R[i, start])

    return reranked


def time_profile(func):
    @wraps(func)
    def arg_wrapper(*args, **kwargs):
        if os.environ.get('NES_PROFILING', False):
            start_t = time.perf_counter()
            r = func(*args, **kwargs)
            elapsed = time.perf_counter() - start_t
            level_prefix = ''.join('-' for v in inspect.stack() if v.index > 0)
            profile_logger.info('%s%s: %3.3fs' % (level_prefix, func.__qualname__, elapsed))
        else:
            r = func(*args, **kwargs)
        return r

    return arg_wrapper


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


class SentenceSplitter:
    def __init__(self, min_len=2, max_len=20):
        self.min_len = min_len
        self.max_len = max_len
        self.must_split = r"[.。！？!?]+"
        self.maybe_split = r"[,，、.。:：;；(（)）\s]+"

    def _is_ascii(self, s):
        return len(s) == len(s.encode())

    def _get_printable(self, p):
        p = html.unescape(p)  # decode html entity
        p = ''.join(c for c in p if c.isprintable())  # remove unprintable char
        p = ''.join(p.split())  # remove space
        return p

    def _check_p(self, p):
        if (len(p) > self.min_len and  # must longer
                not self._is_ascii(p) and  # must not all english
                # len(re.findall('\s', p)) == 0 and  # must not contain spaces -> likely spam
                '\\x' not in p):  # must not contain bad unicode char
            return True

    def _split(self, p, reg):
        sent = [s for s in re.split(reg, self._get_printable(p)) if s.strip()]
        for s in sent:
            if self._check_p(s):
                if len(s) > self.max_len and reg != self.maybe_split:
                    for ss in self._split(s, self.maybe_split):
                        yield ss
                else:
                    yield s

    def split(self, p):
        return self._split(p, self.must_split)


def batch_iterator(it: Iterator[Any], batch_size: int) -> Iterator[Any]:
    if not batch_size or batch_size <= 0:
        return it
    it = iter(it)
    while True:
        chunk = tuple(islice(it, batch_size))
        if not chunk:
            return
        yield chunk


cn_sent_splitter = SentenceSplitter(max_len=5)
profile_logger = set_logger('PROFILE')
doc_logger = set_logger('DOC')
