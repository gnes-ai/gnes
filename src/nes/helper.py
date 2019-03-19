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
from typing import Iterator, Any, Union, List, Callable

import numpy as np
from joblib import Memory
from memory_profiler import memory_usage
from psutil import virtual_memory
from ruamel.yaml import YAML
from termcolor import colored

__all__ = ['get_sys_info', 'get_optimal_sample_size',
           'get_perm', 'time_profile', 'set_logger',
           'get_args_parser',
           'batch_iterator', 'batching',
           'get_run_args',
           'yaml',
           'cn_sent_splitter',
           'profile_logger',
           'doc_logger',
           'parse_arg']


def get_sys_info():
    mem = virtual_memory()
    # get available memory in (M)
    avai = mem.available / 1e6

    def timer(x, y):
        stime = time.time()
        c = np.matmul(x, y)
        return time.time() - stime

    x = np.random.random([1000, 1000])
    y = np.random.random([1000, 1000])
    unit_time = timer(x, y)
    return avai, unit_time


def ralloc_estimator(n_lines, num_dim, unit_time, max_mem, max_time=60):
    est_time = num_dim * num_dim * n_lines / 1e9 * unit_time * 2
    est_mem = 60 + 30 * (n_lines * num_dim / 768 / 10000)
    if (est_time < max_time) and (est_mem < max_mem * 0.5):
        return n_lines
    else:
        return ralloc_estimator(int(n_lines * 0.9), num_dim, unit_time, max_mem, max_time)


def get_optimal_sample_size(x):
    max_mem, unit_time = get_sys_info()
    num_samples, num_dim = x.shape
    return ralloc_estimator(num_samples, num_dim, unit_time, max_mem, 30)


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
            start_mem = memory_usage()[0]
            r = func(*args, **kwargs)
            elapsed = time.perf_counter() - start_t
            elapsed_mem = memory_usage()[0]
            level_prefix = ''.join('-' for v in inspect.stack() if v and v.index is not None and v.index >= 0)
            profile_logger.info('%s%s: %3.3fs. memory: %4.2fM -> %4.2fM' % (
                level_prefix, func.__qualname__, elapsed, start_mem, elapsed_mem))
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


def batch_iterator(data: Union[Iterator[Any], List[Any], np.ndarray], batch_size: int, axis: int = 0) -> Iterator[Any]:
    if not batch_size or batch_size <= 0:
        yield data
        return
    if isinstance(data, np.ndarray):
        if batch_size >= data.shape[axis]:
            yield data
            return
        for _ in range(0, data.shape[axis], batch_size):
            start = _
            end = min(len(data), _ + batch_size)
            yield np.take(data, range(start, end), axis, mode='clip')
    elif hasattr(data, '__len__'):
        if batch_size >= len(data):
            yield data
            return
        for _ in range(0, len(data), batch_size):
            yield data[_:_ + batch_size]
    elif isinstance(data, Iterator):
        # as iterator, there is no way to know the length of it
        while True:
            chunk = tuple(islice(data, batch_size))
            if not chunk:
                return
            yield chunk
    else:
        raise TypeError('unsupported type: %s' % type(data))


def get_size(data: Union[Iterator[Any], List[Any], np.ndarray], axis: int = 0) -> int:
    if isinstance(data, np.ndarray):
        total_size = data.shape[axis]
    elif hasattr(data, '__len__'):
        total_size = len(data)
    else:
        total_size = None
    return total_size


def batching(func: Callable[[Any], np.ndarray] = None, *,
             batch_size: Union[int, Callable] = None, num_batch=None,
             axis: int = 0):
    def _batching(func):
        @wraps(func)
        def arg_wrapper(self, data, *args, **kwargs):
            # priority: decorator > class_attribute
            b_size = (batch_size(data) if callable(batch_size) else batch_size) or getattr(self, 'batch_size', None)
            # no batching if b_size is None
            if b_size is None:
                return func(self, data, *args, **kwargs)

            if hasattr(self, 'logger'):
                self.logger.info(
                    'batching enabled for %s(). batch_size=%s\tnum_batch=%s\taxis=%s' % (
                        func.__qualname__, b_size, num_batch, axis))

            total_size1 = get_size(data, axis)
            total_size2 = b_size * num_batch if num_batch else None

            if total_size1 is not None and total_size2 is not None:
                total_size = min(total_size1, total_size2)
            else:
                total_size = total_size1 or total_size2

            final_result = None

            done_size = 0
            for b in batch_iterator(data[:total_size], b_size, axis):
                r = func(self, b, *args, **kwargs)
                if isinstance(r, np.ndarray):
                    # first result kicks in
                    if final_result is None:
                        if total_size is None:
                            final_result = []
                        else:
                            d_shape = list(r.shape)
                            d_shape[axis] = total_size
                            final_result = np.zeros(d_shape, dtype=r.dtype)

                    # fill the data into final_result
                    cur_size = get_size(r)

                    if total_size is None:
                        final_result.append(r)
                    else:
                        final_result[done_size:(done_size + cur_size)] = r

                    done_size += cur_size

                    if total_size is not None and done_size >= total_size:
                        break

            if isinstance(final_result, list):
                final_result = np.concatenate(final_result, 0)
            return final_result

        return arg_wrapper

    if func:
        return _batching(func)
    else:
        return _batching


class MemoryCache:
    def __init__(self, cache_path: str = None):
        self._cache_path = cache_path
        if self._cache_path:
            self._memory = Memory(self._cache_path, verbose=0)
        else:
            self._memory = None

    def __call__(self, func):
        if self._memory:
            return self._memory.cache(func)
        else:
            return func

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['_memory']
        return d

    def __setstate__(self, d):
        self.__dict__.update(d)
        if self._cache_path:
            self._memory = Memory(self._cache_path, verbose=0)
        else:
            self._memory = None

    def clear(self):
        if self._memory:
            self._memory.clear()

    def disable(self):
        self._memory = None

    def enable(self):
        if not self._memory:
            self._memory = Memory(self._cache_path, verbose=0)


def _get_yaml():
    y = YAML(typ='safe')
    y.default_flow_style = False
    return y


def parse_arg(v: str):
    if v.startswith('[') and v.endswith(']'):
        # function args must be immutable tuples not list
        tmp = v.replace('[', '').replace(']', '').strip().split(',')
        if len(tmp) > 0:
            return [parse_arg(vv.strip()) for vv in tmp]
        else:
            return []
    try:
        v = int(v)  # parse int parameter
    except ValueError:
        try:
            v = float(v)  # parse float parameter
        except ValueError:
            if len(v) == 0:
                # ignore it when the parameter is empty
                v = None
            elif v.lower() == 'true':  # parse boolean parameter
                v = True
            elif v.lower() == 'false':
                v = False
    return v


cn_sent_splitter = SentenceSplitter(max_len=5)
profile_logger = set_logger('PROFILE')
doc_logger = set_logger('DOC')

yaml = _get_yaml()
