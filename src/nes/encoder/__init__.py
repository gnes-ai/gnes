import os
import pickle
import time
from functools import wraps

from ..helper import set_logger


class BaseEncoder:
    def __init__(self, *args, **kwargs):
        # common
        self.is_trained = False
        self.verbose = 'verbose' in kwargs and kwargs['verbose']
        self.logger = set_logger(self.__class__.__name__, self.verbose)

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['logger']
        return d

    def __setstate__(self, d):
        self.__dict__.update(d)
        self.logger = set_logger(self.__class__.__name__, self.verbose)

    def _train_required(func):
        @wraps(func)
        def arg_wrapper(self, *args, **kwargs):
            if self.is_trained:
                return func(self, *args, **kwargs)
            else:
                raise RuntimeError('training is required before calling "%s"' % func.__name__)

        return arg_wrapper

    def _as_train_func(func):
        @wraps(func)
        def arg_wrapper(self, *args, **kwargs):
            if self.is_trained:
                self.logger.warning('"%s" has been trained already, '
                                    'training it again will override the previous training' % self.__class__.__name__)
            f = func(self, *args, **kwargs)
            self.is_trained = True
            return f

        return arg_wrapper

    def _timeit(func):
        @wraps(func)
        def arg_wrapper(self, *args, **kwargs):
            if os.environ.get('NES_BENCHMARK', False):
                start_t = time.perf_counter()
                r = func(self, *args, **kwargs)
                elapsed = time.perf_counter() - start_t
                self.logger.info('%s.%s: %3.3fs' % (self.__class__.__name__, func.__name__, elapsed))
            else:
                r = func(self, *args, **kwargs)
            return r

        return arg_wrapper

    @_timeit
    def dump(self, filename: str):
        with open(filename, 'wb') as fp:
            pickle.dump(self, fp)

    def load(filename: str) -> 'BaseEncoder':
        with open(filename, 'rb') as fp:
            return pickle.load(fp)

    @_timeit
    def encode(self, *args, **kwargs):
        pass

    @_timeit
    def train(self, *args, **kwargs):
        pass

    _timeit = staticmethod(_timeit)
    _as_train_func = staticmethod(_as_train_func)
    _train_required = staticmethod(_train_required)
    load = staticmethod(load)


class BaseBinaryEncoder(BaseEncoder):
    def encode(self, *args, **kwargs) -> bytes: pass
