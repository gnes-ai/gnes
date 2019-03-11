import pickle
from functools import wraps
from typing import TypeVar

from ..helper import set_logger, time_profile, MemoryCache

_tb = TypeVar('T', bound='TrainableBase')


class TrainableBase:
    _timeit = time_profile

    def __init__(self, *args, **kwargs):
        # common
        self.is_trained = False
        self.verbose = 'verbose' in kwargs and kwargs['verbose']
        self.logger = set_logger(self.__class__.__name__, self.verbose)
        self.memcached = MemoryCache(cache_path='.nes_cache')

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['logger']
        return d

    def __setstate__(self, d):
        self.__dict__.update(d)
        self.logger = set_logger(self.__class__.__name__, self.verbose)

    @staticmethod
    def _train_required(func):
        @wraps(func)
        def arg_wrapper(self, *args, **kwargs):
            if self.is_trained:
                return func(self, *args, **kwargs)
            else:
                raise RuntimeError('training is required before calling "%s"' % func.__name__)

        return arg_wrapper

    @staticmethod
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

    @staticmethod
    def _pipeline(is_train=False):
        def _pipeline_inner(func):
            @wraps(func)
            def arg_wrapper(self, data, *args, **kwargs):
                for be in self.pipeline:
                    if is_train:
                        be.train(data, *args, **kwargs)
                    data = be.encode(data, *args, **kwargs)
                return func(self, data, *args, **kwargs)

            return arg_wrapper

        return _pipeline_inner

    def train(self, *args, **kwargs):
        raise NotImplementedError

    @_timeit
    def dump(self, filename: str) -> None:
        with open(filename, 'wb') as fp:
            pickle.dump(self, fp)

    @staticmethod
    @_timeit
    def load(filename: str) -> _tb:
        with open(filename, 'rb') as fp:
            return pickle.load(fp)

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
