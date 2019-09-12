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

import fcntl
import importlib.util
import logging
import os
import sys
import time
from copy import copy
from functools import wraps
from itertools import islice
from logging import Formatter
from typing import Iterator, Any, Union, List, Callable

import numpy as np

try:
    from memory_profiler import memory_usage
except ImportError:
    memory_usage = lambda: [0]

from ruamel.yaml import YAML
from termcolor import colored

__all__ = ['get_sys_info', 'get_optimal_sample_size',
           'get_perm', 'time_profile', 'set_logger',
           'batch_iterator', 'batching', 'yaml',
           'profile_logger', 'load_contrib_module',
           'parse_arg', 'profiling', 'FileLock',
           'train_required', 'get_first_available_gpu',
           'PathImporter', 'progressbar']


def progressbar(i, prefix="", suffix="", count=100, size=60):
    """

    Example:

    for i in range(10000):
        progressbar(i, prefix="computing: ", count=100, size=60)

    The resulted output is:
        computing: [###########################################################.] 99/100
        computing: [###########################################################.] 199/200
        computing: [###########################################################.] 299/300
        computing: [###########################################################.] 399/400
        computing: [###########################################################.] 499/500
        computing: [###########################################################.] 599/600
        computing: [###########################################################.] 699/700
        computing: [###########################################################.] 799/800
        computing: [###########################################################.] 899/900
        computing: [#############################...............................] 950/1000
    """
    step = int(i / count)
    _i = i
    i = i % count
    if step > 0 and i == 0:
        sys.stdout.write('\n')
    x = int(size * i / count)
    sys.stdout.write(
        "%s[%s%s] %i/%i %s\r" % (prefix, "#" * x, "." * (size - x), _i,
                                   (step + 1) * count, suffix))
    sys.stdout.flush()

def get_first_available_gpu():
    try:
        import GPUtil
        r = GPUtil.getAvailable(order='random',
                                maxMemory=0.5,
                                maxLoad=0.5,
                                limit=1)
        if r:
            return r[0]
        raise ValueError
    except ImportError:
        return -1
    except ValueError:
        return -1


class FileLock:
    """
    Implements the Posix based file locking (Linux, Ubuntu, MacOS, etc.)
    """

    def __init__(self, lock_file: str = "LOCK"):
        self._lock_file = lock_file
        self._lock_file_fd = None

    @property
    def is_locked(self):
        return self._lock_file_fd is not None

    def acquire(self):
        open_mode = os.O_RDWR | os.O_CREAT | os.O_TRUNC
        fd = os.open(self._lock_file, open_mode)

        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._lock_file_fd = fd
            return fd
        except (IOError, OSError):
            os.close(fd)
        return None

    def release(self):
        if self.is_locked:
            fd = self._lock_file_fd
            self._lock_file_fd = None
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)


def get_sys_info():
    from psutil import virtual_memory
    mem = virtual_memory()
    # get available memory in (M)
    avai = mem.available / 1e6

    def timer(x, y):
        stime = time.time()
        np.matmul(x, y)
        return time.time() - stime

    x = np.random.random([1000, 1000])
    y = np.random.random([1000, 1000])
    unit_time = timer(x, y)
    return avai, unit_time


def touch_dir(base_dir: str) -> None:
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)


def ralloc_estimator(n_lines, num_dim, unit_time, max_mem, max_time=60):
    est_time = num_dim * num_dim * n_lines / 1e9 * unit_time * 2
    est_mem = 60 + 30 * (n_lines * num_dim / 768 / 10000)
    if (est_time < max_time) and (est_mem < max_mem * 0.5):
        return n_lines
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
        if os.environ.get('GNES_PROFILING', False):
            start_t = time.perf_counter()
            if os.environ.get('GNES_PROFILING_MEM', False):
                start_mem = memory_usage()[0]
            r = func(*args, **kwargs)
            elapsed = time.perf_counter() - start_t
            if os.environ.get('GNES_PROFILING_MEM', False):
                end_mem = memory_usage()[0]
            # level_prefix = ''.join('-' for v in inspect.stack() if v and v.index is not None and v.index >= 0)
            level_prefix = ''
            if os.environ.get('GNES_PROFILING_MEM', False):
                mem_status = 'memory: %4.2fM -> %4.2fM' % (start_mem, end_mem)
            else:
                mem_status = ''
            profile_logger.info('%s%s: %3.3fs. %s' % (level_prefix, func.__qualname__, elapsed, mem_status))
        else:
            r = func(*args, **kwargs)
        return r

    return arg_wrapper


class ColoredFormatter(Formatter):
    MAPPING = {
        'DEBUG': dict(color='white', on_color=None),  # white
        'INFO': dict(color='white', on_color=None),  # cyan
        'WARNING': dict(color='yellow', on_color='on_grey'),  # yellow
        'ERROR': dict(color='white', on_color='on_red'),  # 31 for red
        'CRITICAL': dict(color='white', on_color='on_green'),  # white on red bg
    }

    PREFIX = '\033['
    SUFFIX = '\033[0m'

    def format(self, record):
        cr = copy(record)
        seq = self.MAPPING.get(cr.levelname, self.MAPPING['INFO'])  # default white
        cr.msg = colored(cr.msg, **seq)
        return super().format(cr)


def set_logger(context, verbose=False):
    if os.name == 'nt':  # for Windows
        return NTLogger(context, verbose)

    # Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logger = logging.getLogger(context)
    logger.propagate = False
    if not logger.handlers:
        logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        formatter = ColoredFormatter(
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


class TimeContext:
    def __init__(self, msg: str, logger=None):
        self._msg = msg
        self._logger = logger
        self.duration = 0

    def __enter__(self):
        self.start = time.perf_counter()
        if not self._logger:
            print(self._msg, end=' ...\t', flush=True)
        return self

    def __exit__(self, typ, value, traceback):
        self.duration = time.perf_counter() - self.start
        if self._logger:
            self._logger.info('%s takes %3.3f secs' % (self._msg, self.duration))
        else:
            print(colored('    [%3.3f secs]' % self.duration, 'green'), flush=True)


class Tokenizer:
    def __init__(self, dict_path: str = None):
        import jieba
        self._jieba = jieba.Tokenizer()
        self._jieba.cache_file = "gnes.jieba_wrapper.cache"

        if dict_path is not None:
            self._jieba.load_userdict(dict_path)

    def tokenize(self, text, with_position=False):
        if not with_position:
            return self._jieba.lcut(text)  # resulted token list
        else:
            return self._jieba.tokenize(text)  # triple data consisting of (token, start_pos, end_pos)


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


def pooling_simple(data_array, pooling_strategy):
    if pooling_strategy == 'REDUCE_MEAN':
        _pooled_data = sum(data_array) / (len(data_array) + 1e-10)
    elif pooling_strategy == 'REDUCE_MAX':
        _pooled_data = max(data_array) / (len(data_array) + 1e-10)
    elif pooling_strategy == 'REDUCE_MEAN_MAX':
        _pooled_data = np.concatenate(
            (sum(data_array) / (len(data_array) + 1e-10),
             max(data_array) / (len(data_array) + 1e-10)), axis=0)
    else:
        raise ValueError('pooling_strategy: %s has not been implemented' % pooling_strategy)
    return _pooled_data


def pooling_torch(data_tensor, mask_tensor, pooling_strategy):
    import torch

    minus_mask = lambda x, m: x - (1.0 - m).unsqueeze(2) * 1e30
    mul_mask = lambda x, m: torch.mul(x, m.unsqueeze(2))

    masked_reduce_mean = lambda x, m: torch.div(torch.sum(mul_mask(x, m), dim=1),
                                                torch.sum(m.unsqueeze(2), dim=1) + 1e-10)
    masked_reduce_max = lambda x, m: torch.max(minus_mask(x, m), 1)[0]

    if pooling_strategy == 'REDUCE_MEAN':
        output_tensor = masked_reduce_mean(data_tensor, mask_tensor)
    elif pooling_strategy == 'REDUCE_MAX':
        output_tensor = masked_reduce_max(data_tensor, mask_tensor)
    elif pooling_strategy == 'REDUCE_MEAN_MAX':
        output_tensor = torch.cat(
            (masked_reduce_mean(data_tensor, mask_tensor),
             masked_reduce_max(data_tensor, mask_tensor)), dim=1)
    else:
        raise ValueError('pooling_strategy: %s has not been implemented' % pooling_strategy)

    return output_tensor


def batching(func: Callable[[Any], np.ndarray] = None, *,
             batch_size: Union[int, Callable] = None, num_batch=None,
             iter_axis: int = 0, concat_axis: int = 0, chunk_dim=-1):
    def _batching(func):
        @wraps(func)
        def arg_wrapper(self, data, label=None, *args, **kwargs):
            # priority: decorator > class_attribute
            b_size = (batch_size(data) if callable(batch_size) else batch_size) or getattr(self, 'batch_size', None)
            # no batching if b_size is None
            if b_size is None:
                if label is None:
                    return func(self, data, *args, **kwargs)
                else:
                    return func(self, data, label, *args, **kwargs)

            if hasattr(self, 'logger'):
                self.logger.info(
                    'batching enabled for %s(). batch_size=%s\tnum_batch=%s\taxis=%s' % (
                        func.__qualname__, b_size, num_batch, iter_axis))

            total_size1 = get_size(data, iter_axis)
            total_size2 = b_size * num_batch if num_batch else None

            if total_size1 is not None and total_size2 is not None:
                total_size = min(total_size1, total_size2)
            else:
                total_size = total_size1 or total_size2

            final_result = []

            if label is not None:
                data = (data, label)

            for b in batch_iterator(data[:total_size], b_size, iter_axis):
                if label is None:
                    r = func(self, b, *args, **kwargs)
                else:
                    r = func(self, b[0], b[1], *args, **kwargs)

                if r is not None:
                    final_result.append(r)

            if len(final_result) == 1:
                # the only result of one batch
                return final_result[0]

            if len(final_result) and concat_axis is not None:
                if isinstance(final_result[0], np.ndarray):
                    final_result = np.concatenate(final_result, concat_axis)
                    if chunk_dim != -1:
                        final_result = final_result.reshape((-1, chunk_dim, final_result.shape[1]))
                elif isinstance(final_result[0], tuple):
                    reduced_result = []
                    num_cols = len(final_result[0])
                    for col in range(num_cols):
                        reduced_result.append(np.concatenate([row[col] for row in final_result], concat_axis))
                    if chunk_dim != -1:
                        for col in range(num_cols):
                            reduced_result[col] = reduced_result[col].reshape(
                                (-1, chunk_dim, reduced_result[col].shape[1]))
                    final_result = tuple(reduced_result)

            if len(final_result):
                return final_result

        return arg_wrapper

    if func:
        return _batching(func)
    else:
        return _batching


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


def countdown(t: int, logger=None, reason: str = 'I am blocking this thread'):
    if not logger:
        sys.stdout.write('\n')
        sys.stdout.flush()
    while t > 0:
        t -= 1
        msg = '%ss left: %s' % (colored('%3d' % t, 'yellow'), reason)
        if logger:
            logger.info(msg)
        else:
            sys.stdout.write('\r%s' % msg)
            sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write('\n')
    sys.stdout.flush()


def as_numpy_array(func, dtype=np.float32):
    @wraps(func)
    def arg_wrapper(self, *args, **kwargs):
        r = func(self, *args, **kwargs)
        r_type = type(r).__name__
        if r_type in {'ndarray', 'EagerTensor', 'Tensor', 'list'}:
            return np.array(r, dtype)
        else:
            raise TypeError('unrecognized type %s: %s' % (r_type, type(r)))

    return arg_wrapper


def train_required(func):
    @wraps(func)
    def arg_wrapper(self, *args, **kwargs):
        if hasattr(self, 'is_trained'):
            if self.is_trained:
                return func(self, *args, **kwargs)
            else:
                raise RuntimeError('training is required before calling "%s"' % func.__name__)
        else:
            raise AttributeError('%r has no attribute "is_trained"' % self)

    return arg_wrapper


def load_contrib_module():
    if not os.getenv('GNES_CONTRIB_MODULE_IS_LOADING'):
        import importlib.util

        contrib = os.getenv('GNES_CONTRIB_MODULE')
        os.environ['GNES_CONTRIB_MODULE_IS_LOADING'] = 'true'

        modules = []

        if contrib:
            default_logger.info(
                'find a value in $GNES_CONTRIB_MODULE=%s, will load them as external modules' % contrib)
            for p in contrib.split(','):
                m = PathImporter.add_modules(p)
                modules.append(m)
                default_logger.info('successfully registered %s class, you can now use it via yaml.' % m)
        return modules


class PathImporter:

    @staticmethod
    def _get_module_name(absolute_path):
        module_name = os.path.basename(absolute_path)
        module_name = module_name.replace('.py', '')
        return module_name

    @staticmethod
    def add_modules(*paths):
        for p in paths:
            if not os.path.exists(p):
                raise FileNotFoundError('cannot import module from %s, file not exist', p)
            module, spec = PathImporter._path_import(p)
        return module

    @staticmethod
    def _path_import(absolute_path):
        module_name = PathImporter._get_module_name(absolute_path)
        spec = importlib.util.spec_from_file_location(module_name, absolute_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[spec.name] = module
        return module, spec


profile_logger = set_logger('PROFILE')
default_logger = set_logger('GNES')
profiling = time_profile

yaml = _get_yaml()
