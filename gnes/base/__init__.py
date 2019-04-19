import inspect
import os
import pickle
import re
import tempfile
from functools import wraps
from typing import Dict, Any, Union, TextIO, TypeVar, Type

import ruamel.yaml.constructor

from ..helper import set_logger, profiling, yaml, parse_arg

__all__ = ['train_required', 'TrainableBase']

T = TypeVar('T', bound='TrainableBase')


def import_class_by_str(name: str):
    def _import(module_name, class_name):
        import importlib

        cls2file = getattr(importlib.import_module('gnes.%s' % module_name), '_cls2file_map')
        if class_name in cls2file:
            return getattr(importlib.import_module('gnes.%s.%s' % (module_name, cls2file[class_name])), class_name)

    r = _import('encoder', name) or _import('indexer', name)
    if r:
        return r
    else:
        raise ImportError('Can not locate any class with name: %s, misspelling?' % name)


class TrainableType(type):
    default_property = {
        'is_trained': False,
        'batch_size': None,
        'dump_path': None
    }

    def __new__(meta, *args, **kwargs):
        cls = super().__new__(meta, *args, **kwargs)
        cls.__init__ = meta._store_init_kwargs(cls.__init__)
        if os.environ.get('NES_PROFILING', False):
            for f_name in ['train', 'encode', 'add', 'query']:
                if getattr(cls, f_name, None):
                    setattr(cls, f_name, profiling(getattr(cls, f_name)))

        if getattr(cls, 'train', None):
            setattr(cls, 'train', meta._as_train_func(getattr(cls, 'train')))

        yaml.register_class(cls)
        return cls

    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)

        for k, v in TrainableType.default_property.items():
            if not hasattr(obj, k):
                setattr(obj, k, v)
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
            taboo = {'self', 'args', 'kwargs'}
            all_pars = inspect.signature(func).parameters
            tmp = {k: v.default for k, v in all_pars.items() if k not in taboo}
            tmp_list = [k for k in all_pars.keys() if k not in taboo]
            # set args by aligning tmp_list with arg values
            for k, v in zip(tmp_list, args):
                tmp[k] = v
            # set kwargs
            for k, v in kwargs.items():
                if k in tmp:
                    tmp[k] = v

            if self.store_args_kwargs:
                if args: tmp['args'] = args
                if kwargs: tmp['kwargs'] = kwargs

            if getattr(self, '_init_kwargs_dict', None):
                self._init_kwargs_dict.update(tmp)
            else:
                self._init_kwargs_dict = tmp
            f = func(self, *args, **kwargs)
            return f

        return arg_wrapper


class TrainableBase(metaclass=TrainableType):
    store_args_kwargs = False

    def __init__(self, *args, **kwargs):
        self.is_trained = False
        self.dump_path = None
        self.verbose = 'verbose' in kwargs and kwargs['verbose']
        self.logger = set_logger(self.__class__.__name__, self.verbose)

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

    def train(self, *args, **kwargs):
        pass

    @profiling
    def dump(self, filename: str = None) -> None:
        f = filename or self.dump_path
        if not f:
            f = tempfile.NamedTemporaryFile('w', delete=False, dir=os.environ.get('NES_TEMP_DIR', None)).name
            self.dump_path = f
        with open(f, 'wb') as fp:
            pickle.dump(self, fp)
        self.logger.info('model is dump to %s' % f)

    @profiling
    def dump_yaml(self, filename: str = None) -> None:
        f = filename or self.dump_path
        if f:
            with open(filename, 'w') as fp:
                yaml.dump(self, fp)
        else:
            raise ValueError('please specify a filename or dump_path!')

    @classmethod
    def load_yaml(cls: Type[T], filename: Union[str, TextIO]) -> T:
        if not filename: raise FileNotFoundError
        if isinstance(filename, str):
            with open(filename) as fp:
                return yaml.load(fp)
        else:
            return yaml.load(filename)

    @staticmethod
    @profiling
    def load(filename: str) -> T:
        if not filename: raise FileNotFoundError
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
        tmp = data._dump_instance_to_yaml(data)
        return representer.represent_mapping('!' + cls.__name__, tmp)

    @classmethod
    def from_yaml(cls, constructor, node):
        return cls._get_instance_from_yaml(constructor, node)[0]

    @classmethod
    def _get_instance_from_yaml(cls, constructor, node):
        try:
            data = ruamel.yaml.constructor.SafeConstructor.construct_mapping(
                constructor, node, deep=True)
            cls.init_from_yaml = True

            if cls.store_args_kwargs:
                p = data.get('parameter', {})  # type: Dict[str, Any]
                a = p.pop('args') if 'args' in p else ()
                k = p.pop('kwargs') if 'kwargs' in p else {}
                # maybe there are some hanging kwargs in "parameter"
                tmp_a = (cls._convert_env_var(v) for v in a)
                tmp_p = {kk: cls._convert_env_var(vv) for kk, vv in {**k, **p}.items()}
                obj = cls(*tmp_a, **tmp_p)
            else:
                tmp_p = {kk: cls._convert_env_var(vv) for kk, vv in data.get('parameter', {}).items()}
                obj = cls(**tmp_p)

            for k, v in data.get('property', {}).items():
                setattr(obj, k, v)

            cls.init_from_yaml = False

            return obj, data
        except ruamel.yaml.constructor.ConstructorError as ce:
            match = re.findall(r"'!(.*)'", ce.problem)[0]
            yaml.register_class(import_class_by_str(match))
            return cls._get_instance_from_yaml(constructor, node)

    @staticmethod
    def _convert_env_var(v):
        if isinstance(v, str):
            return parse_arg(os.path.expandvars(v))
        else:
            return v

    @staticmethod
    def _dump_instance_to_yaml(data):
        # note: we only dump non-default property for the sake of clarity
        p = {k: getattr(data, k) for k, v in TrainableType.default_property.items() if getattr(data, k) != v}
        a = {k: v for k, v in data._init_kwargs_dict.items()}
        r = {}
        if a:
            r['parameter'] = a
        if p:
            r['property'] = p
        return r


train_required = TrainableBase._train_required
