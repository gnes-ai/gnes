import inspect
import os
import pickle
from functools import wraps
from typing import TypeVar

import ruamel.yaml.constructor
from ruamel.yaml import YAML

from ..helper import set_logger, MemoryCache, time_profile

_tb = TypeVar('T', bound='TrainableBase')


class TrainableType(type):
    def __new__(meta, *args, **kwargs):
        cls = super().__new__(meta, *args, **kwargs)
        cls.__init__ = meta._store_init_kwargs(cls.__init__)
        if os.environ.get('NES_PROFILING', False):
            for f_name in ['train', 'encode', 'add', 'query']:
                if getattr(cls, f_name, None):
                    setattr(cls, f_name, time_profile(getattr(cls, f_name)))

        if getattr(cls, 'train', None):
            setattr(cls, 'train', meta._as_train_func(getattr(cls, 'train')))
        return cls

    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)
        if not hasattr(obj, 'is_trained'):
            obj.is_trained = False
        if not hasattr(obj, 'batch_size'):
            obj.batch_size = None
        return obj

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
    def _store_init_kwargs(func):
        @wraps(func)
        def arg_wrapper(self, *args, **kwargs):
            all_pars = inspect.signature(func).parameters
            tmp = {k: v.default for k, v in all_pars.items()}
            default_pars = list(all_pars.items())
            for idx, v in enumerate(args, 1):
                tmp[default_pars[idx][0]] = v
            for k, v in kwargs.items():
                tmp[k] = v

            for k in ['self', 'args', 'kwargs']:
                if k in tmp:
                    tmp.pop(k)

            if getattr(self, '_init_kwargs_dict', None):
                self._init_kwargs_dict.update(tmp)
            else:
                self._init_kwargs_dict = tmp
            f = func(self, *args, **kwargs)
            return f

        return arg_wrapper


class TrainableBase(metaclass=TrainableType):
    _timeit = time_profile

    def __init__(self, *args, **kwargs):
        self.is_trained = False
        self.verbose = 'verbose' in kwargs and kwargs['verbose']
        self.logger = set_logger(self.__class__.__name__, self.verbose)
        self.memcached = MemoryCache(cache_path='.nes_cache')

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['logger']
        del d['memcached']
        return d

    def __setstate__(self, d):
        self.__dict__.update(d)
        self.logger = set_logger(self.__class__.__name__, self.verbose)
        self.memcached = MemoryCache(cache_path='.nes_cache')

    @staticmethod
    def _train_required(func):
        @wraps(func)
        def arg_wrapper(self, *args, **kwargs):
            if self.is_trained:
                return func(self, *args, **kwargs)
            else:
                raise RuntimeError('training is required before calling "%s"' % func.__name__)

        return arg_wrapper

    @_timeit
    def train(self, *args, **kwargs):
        pass

    @_timeit
    def dump(self, filename: str) -> None:
        with open(filename, 'wb') as fp:
            pickle.dump(self, fp)

    @_timeit
    def dump_yaml(self, filename: str) -> None:
        yaml = YAML(typ='unsafe')
        yaml.register_class(self.__class__)
        with open(filename, 'w') as fp:
            yaml.dump(self, fp)

    @classmethod
    def load_yaml(cls, filename: str) -> _tb:
        yaml = YAML(typ='unsafe')
        yaml.register_class(cls)
        with open(filename) as fp:
            return yaml.load(fp)

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

    @classmethod
    def to_yaml(cls, representer, data):
        return representer.represent_mapping('!' + cls.__name__, data._init_kwargs_dict)

    @classmethod
    def from_yaml(cls, constructor, node):
        data = ruamel.yaml.constructor.SafeConstructor.construct_mapping(
            constructor, node, deep=True)
        return cls(**data)
