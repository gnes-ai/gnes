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

# pylint: disable=low-comment-ratio


import inspect
import os
import pickle
import tempfile
import uuid
from functools import wraps
from typing import Dict, Any, Union, TextIO, TypeVar, Type

import ruamel.yaml.constructor

from ..helper import set_logger, profiling, yaml, parse_arg, touch_dir, FileLock

__all__ = ['TrainableBase']

T = TypeVar('T', bound='TrainableBase')


def register_all_class(cls2file_map: Dict):
    for k in cls2file_map:
        try:
            import_class_by_str(k)
        except ImportError:
            pass


def import_class_by_str(name: str):
    def _import(module_name, class_name):
        import importlib

        cls2file = getattr(importlib.import_module('gnes.%s' % module_name), '_cls2file_map')
        if class_name in cls2file:
            return getattr(importlib.import_module('gnes.%s.%s' % (module_name, cls2file[class_name])), class_name)

    search_modules = ['encoder', 'indexer', 'preprocessor', 'router']

    for m in search_modules:
        r = _import(m, name)
        if r:
            return r
    else:
        raise ImportError('Can not locate any class with name: %s, misspelling?' % name)


class TrainableType(type):
    default_property = {
        'is_trained': False,
        'batch_size': None,
    }

    def __new__(cls, *args, **kwargs):
        _cls = super().__new__(cls, *args, **kwargs)
        return cls.register_class(_cls)

    def __call__(cls, *args, **kwargs):
        # do _preload_package
        getattr(cls, '_pre_init', lambda *x: None)()

        obj = type.__call__(cls, *args, **kwargs)

        # set attribute
        for k, v in TrainableType.default_property.items():
            if not hasattr(obj, k):
                setattr(obj, k, v)

        # do _post_init()
        getattr(obj, '_post_init_wrapper', lambda *x: None)()
        return obj

    @staticmethod
    def register_class(cls):
        # print('try to register class: %s' % cls.__name__)
        reg_cls_set = getattr(cls, '_registered_class', set())
        if cls.__name__ not in reg_cls_set:
            # print('reg class: %s' % cls.__name__)
            cls.__init__ = TrainableType._store_init_kwargs(cls.__init__)
            if os.environ.get('GNES_PROFILING', False):
                for f_name in ['train', 'encode', 'add', 'query']:
                    if getattr(cls, f_name, None):
                        setattr(cls, f_name, profiling(getattr(cls, f_name)))

            if getattr(cls, 'train', None):
                setattr(cls, 'train', TrainableType._as_train_func(getattr(cls, 'train')))

            reg_cls_set.add(cls.__name__)
            setattr(cls, '_registered_class', reg_cls_set)
            yaml.register_class(cls)
        return cls

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
    lock_work_dir = False

    def __init__(self, *args, **kwargs):
        self.is_trained = False
        self._obj_id = str(uuid.uuid4()).split('-')[0]
        self._obj_pickle_name = '%s%s.bin' % (self.__class__.__name__, self._obj_id)
        self._obj_yaml_name = '%s%s.yml' % (self.__class__.__name__, self._obj_id)
        self._work_dir = os.getcwd()
        self.verbose = 'verbose' in kwargs and kwargs['verbose']
        self.logger = set_logger(self.__class__.__name__, self.verbose)
        self._post_init_vars = set()

    def _post_init_wrapper(self):
        _before = set(list(self.__dict__.keys()))
        self.post_init()
        self._post_init_vars = {k for k in self.__dict__ if k not in _before}

    def post_init(self):
        pass

    @classmethod
    def pre_init(cls):
        pass

    @property
    def pickle_full_path(self):
        return os.path.join(self.work_dir, self._obj_pickle_name)

    @property
    def yaml_full_path(self):
        return os.path.join(self.work_dir, self._obj_yaml_name)

    @property
    def work_dir(self):
        return self._work_dir

    @work_dir.setter
    def work_dir(self, value: str):
        touch_dir(value)
        if self.lock_work_dir:
            self._file_lock = FileLock(os.path.join(value, "LOCK"))
            if self._file_lock.acquire() is None:
                raise RuntimeError(
                    "this model\'s work_dir %r is used and locked by another model" %
                    value)
        self._work_dir = value

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['logger']
        if '_file_lock' in d:
            del d['_file_lock']
        for k in self._post_init_vars:
            del d[k]
        return d

    def __setstate__(self, d):
        self.__dict__.update(d)
        self.logger = set_logger(self.__class__.__name__, self.verbose)
        if self.lock_work_dir:
            # trigger the lock again
            self.work_dir = self._work_dir
        try:
            self._post_init_wrapper()
        except ImportError:
            self.logger.info('ImportError is often caused by a missing component, '
                             'which often can be solved by "pip install" relevant package.')

    def train(self, *args, **kwargs):
        pass

    @profiling
    def dump(self, filename: str = None) -> None:
        f = filename or self.pickle_full_path
        if not f:
            f = tempfile.NamedTemporaryFile('w', delete=False, dir=os.environ.get('NES_TEMP_DIR', None)).name
        with open(f, 'wb') as fp:
            pickle.dump(self, fp)
        self.logger.info('model is pickled to %s' % f)

    @profiling
    def dump_yaml(self, filename: str = None) -> None:
        f = filename or self.yaml_full_path
        if not f:
            f = tempfile.NamedTemporaryFile('w', delete=False, dir=os.environ.get('NES_TEMP_DIR', None)).name
        with open(filename, 'w') as fp:
            yaml.dump(self, fp)
        self.logger.info('model\'s yaml config is dump to %s' % f)

    @classmethod
    def load_yaml(cls: Type[T], filename: Union[str, TextIO]) -> T:
        if not filename: raise FileNotFoundError
        if isinstance(filename, str):
            with open(filename) as fp:
                return yaml.load(fp)
        else:
            with filename:
                return yaml.load(filename)

    @staticmethod
    @profiling
    def load(filename: str) -> T:
        if not filename: raise FileNotFoundError
        with open(filename, 'rb') as fp:
            return pickle.load(fp)

    def close(self):
        if self.lock_work_dir:
            self._file_lock.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @staticmethod
    def _get_tags_from_node(node):
        def node_recurse_generator(n):
            if n.tag.startswith('!'):
                yield n.tag.lstrip('!')
            for nn in n.value:
                if isinstance(nn, tuple):
                    for k in nn:
                        yield from node_recurse_generator(k)
                elif isinstance(nn, ruamel.yaml.nodes.Node):
                    yield from node_recurse_generator(nn)

        return list(set(list(node_recurse_generator(node))))

    @classmethod
    def to_yaml(cls, representer, data):
        tmp = data._dump_instance_to_yaml(data)
        return representer.represent_mapping('!' + cls.__name__, tmp)

    @classmethod
    def from_yaml(cls, constructor, node, stop_on_import_error=False):
        return cls._get_instance_from_yaml(constructor, node, stop_on_import_error)[0]

    @classmethod
    def _get_instance_from_yaml(cls, constructor, node, stop_on_import_error=False):
        try:
            for c in cls._get_tags_from_node(node):
                import_class_by_str(c)
        except ImportError as ex:
            if stop_on_import_error:
                raise RuntimeError('Cannot import module, pip install may required') from ex

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
            old = getattr(obj, k, None)
            setattr(obj, k, v)
            if old and old != v:
                obj.logger.info('property: %r is replaced from %r to %r' % (k, old, v))

        cls.init_from_yaml = False

        return obj, data

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
