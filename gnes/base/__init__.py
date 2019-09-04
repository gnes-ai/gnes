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


import inspect
import os
import pickle
import tempfile
import uuid
from functools import wraps
from typing import Dict, Any, Union, TextIO, TypeVar, Type, List, Callable

import ruamel.yaml.constructor

from ..helper import set_logger, profiling, yaml, parse_arg, load_contrib_module

__all__ = ['TrainableBase', 'CompositionalTrainableBase']

T = TypeVar('T', bound='TrainableBase')


def register_all_class(cls2file_map: Dict, module_name: str):
    import importlib
    for k, v in cls2file_map.items():
        try:
            getattr(importlib.import_module('gnes.%s.%s' % (module_name, v)), k)
        except ImportError as ex:
            default_logger = set_logger('GNES')
            default_logger.warning('fail to register %s, due to "%s", you will not be able to use this model' % (k, ex))
    load_contrib_module()


def import_class_by_str(name: str):
    def _import(module_name, class_name):
        import importlib

        cls2file = getattr(importlib.import_module('gnes.%s' % module_name), '_cls2file_map')
        if class_name in cls2file:
            return getattr(importlib.import_module('gnes.%s.%s' % (module_name, cls2file[class_name])), class_name)

    search_modules = ['encoder', 'indexer', 'preprocessor', 'router', 'score_fn']

    for m in search_modules:
        r = _import(m, name)
        if r:
            return r
    else:
        raise ImportError('Can not locate any class with name: %s, misspelling?' % name)


class TrainableType(type):
    default_gnes_config = {
        'is_trained': False,
        'batch_size': None,
        'work_dir': os.environ.get('GNES_VOLUME', os.getcwd()),
        'name': None,
        'on_gpu': False,
        'warn_unnamed': True
    }

    def __new__(cls, *args, **kwargs):
        _cls = super().__new__(cls, *args, **kwargs)
        return cls.register_class(_cls)

    def __call__(cls, *args, **kwargs):
        # do _preload_package
        getattr(cls, '_pre_init', lambda *x: None)()

        if 'gnes_config' in kwargs:
            gnes_config = kwargs.pop('gnes_config')
        else:
            gnes_config = {}

        obj = type.__call__(cls, *args, **kwargs)

        # set attribute with priority
        # gnes_config in YAML > class attribute > default_gnes_config
        for k, v in TrainableType.default_gnes_config.items():
            if k in gnes_config:
                v = gnes_config[k]
            v = _expand_env_var(v)
            if not hasattr(obj, k):
                if k == 'is_trained' and isinstance(obj, CompositionalTrainableBase):
                    continue
                setattr(obj, k, v)

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
                # print('registered train func of %s'%cls)
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
            if not isinstance(self, CompositionalTrainableBase):
                self.is_trained = True
            return f

        return arg_wrapper

    @staticmethod
    def _store_init_kwargs(func):
        @wraps(func)
        def arg_wrapper(self, *args, **kwargs):
            taboo = {'self', 'args', 'kwargs'}
            taboo.update(TrainableType.default_gnes_config.keys())
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
                if kwargs: tmp['kwargs'] = {k: v for k, v in kwargs.items() if k not in taboo}

            if getattr(self, '_init_kwargs_dict', None):
                self._init_kwargs_dict.update(tmp)
            else:
                self._init_kwargs_dict = tmp
            f = func(self, *args, **kwargs)
            return f

        return arg_wrapper


class TrainableBase(metaclass=TrainableType):
    """
    The base class for preprocessor, encoder, indexer and router

    """
    store_args_kwargs = False

    def __init__(self, *args, **kwargs):
        self.verbose = 'verbose' in kwargs and kwargs['verbose']
        self.logger = set_logger(self.__class__.__name__, self.verbose)
        self._post_init_vars = set()

    def _post_init_wrapper(self):
        if not getattr(self, 'name', None) and os.environ.get('GNES_WARN_UNNAMED_COMPONENT', '1') == '1':
            _id = str(uuid.uuid4()).split('-')[0]
            _name = '%s-%s' % (self.__class__.__name__, _id)
            if self.warn_unnamed:
                self.logger.warning(
                    'this object is not named ("name" is not found under "gnes_config" in YAML config), '
                    'i will call it "%s". '
                    'naming the object is important as it provides an unique identifier when '
                    'serializing/deserializing this object.' % _name)
            setattr(self, 'name', _name)

        _before = set(list(self.__dict__.keys()))
        self.post_init()
        self._post_init_vars = {k for k in self.__dict__ if k not in _before}

    def post_init(self):
        """
        Declare class attributes/members that can not be serialized in standard way

        """
        pass

    @classmethod
    def pre_init(cls):
        pass

    @property
    def dump_full_path(self):
        """
        Get the binary dump path

        :return:
        """
        return os.path.join(self.work_dir, '%s.bin' % self.name)

    @property
    def yaml_full_path(self):
        """
        Get the file path of the yaml config
        :return:
        """
        return os.path.join(self.work_dir, '%s.yml' % self.name)

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['logger']
        for k in self._post_init_vars:
            del d[k]
        return d

    def __setstate__(self, d):
        self.__dict__.update(d)
        self.logger = set_logger(self.__class__.__name__, self.verbose)
        try:
            self._post_init_wrapper()
        except ImportError as ex:
            self.logger.warning('ImportError is often caused by a missing component, '
                                'which often can be solved by "pip install" relevant package. %s' % ex, exc_info=True)

    def train(self, *args, **kwargs):
        """
        Train the model, need to be overrided
        """
        pass

    @profiling
    def dump(self, filename: str = None) -> None:
        """
        Serialize the object to a binary file
        :param filename: file path of the serialized file, if not given then `self.dump_full_path` is used
        """
        f = filename or self.dump_full_path
        if not f:
            f = tempfile.NamedTemporaryFile('w', delete=False, dir=os.environ.get('GNES_VOLUME', None)).name
        with open(f, 'wb') as fp:
            pickle.dump(self, fp)
        self.logger.critical('model is serialized to %s' % f)

    @profiling
    def dump_yaml(self, filename: str = None) -> None:
        """
        Serialize the object to a yaml file
        :param filename: file path of the yaml file, if not given then `self.dump_yaml_path` is used
        """
        f = filename or self.yaml_full_path
        if not f:
            f = tempfile.NamedTemporaryFile('w', delete=False, dir=os.environ.get('GNES_VOLUME', None)).name
        with open(f, 'w', encoding='utf8') as fp:
            yaml.dump(self, fp)
        self.logger.info('model\'s yaml config is dump to %s' % f)

    @classmethod
    def load_yaml(cls: Type[T], filename: Union[str, TextIO]) -> T:
        if not filename: raise FileNotFoundError
        if isinstance(filename, str):
            with open(filename, encoding='utf8') as fp:
                return yaml.load(fp)
        else:
            with filename:
                return yaml.load(filename)

    @staticmethod
    @profiling
    def load(filename: str = None) -> T:
        if not filename: raise FileNotFoundError
        with open(filename, 'rb') as fp:
            return pickle.load(fp)

    def close(self):
        """
        Release the resources as model is destroyed
        """
        pass

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

        if node.tag in {'!PipelineEncoder', '!CompositionalTrainableBase'}:
            os.environ['GNES_WARN_UNNAMED_COMPONENT'] = '0'

        data = ruamel.yaml.constructor.SafeConstructor.construct_mapping(
            constructor, node, deep=True)

        dump_path = cls._get_dump_path_from_config(data.get('gnes_config', {}))
        load_from_dump = False
        if dump_path:
            obj = cls.load(dump_path)
            obj.logger.critical('restore %s from %s' % (cls.__name__, dump_path))
            load_from_dump = True
        else:
            cls.init_from_yaml = True

            if cls.store_args_kwargs:
                p = data.get('parameters', {})  # type: Dict[str, Any]
                a = p.pop('args') if 'args' in p else ()
                k = p.pop('kwargs') if 'kwargs' in p else {}
                # maybe there are some hanging kwargs in "parameters"
                tmp_a = (_expand_env_var(v) for v in a)
                tmp_p = {kk: _expand_env_var(vv) for kk, vv in {**k, **p}.items()}
                obj = cls(*tmp_a, **tmp_p, gnes_config=data.get('gnes_config', {}))
            else:
                tmp_p = {kk: _expand_env_var(vv) for kk, vv in data.get('parameters', {}).items()}
                obj = cls(**tmp_p, gnes_config=data.get('gnes_config', {}))

            obj.logger.critical('initialize %s from a yaml config' % cls.__name__)
            cls.init_from_yaml = False

        if node.tag in {'!PipelineEncoder', '!CompositionalTrainableBase'}:
            os.environ['GNES_WARN_UNNAMED_COMPONENT'] = '1'

        return obj, data, load_from_dump

    @staticmethod
    def _get_dump_path_from_config(gnes_config: Dict):
        if 'name' in gnes_config:
            dump_path = os.path.join(gnes_config.get('work_dir', os.getcwd()), '%s.bin' % gnes_config['name'])
            if os.path.exists(dump_path):
                return dump_path

    @staticmethod
    def _dump_instance_to_yaml(data):
        # note: we only dump non-default property for the sake of clarity
        p = {k: getattr(data, k) for k, v in TrainableType.default_gnes_config.items() if getattr(data, k) != v}
        a = {k: v for k, v in data._init_kwargs_dict.items() if k not in TrainableType.default_gnes_config}
        r = {}
        if a:
            r['parameters'] = a
        if p:
            r['gnes_config'] = p
        return r

    def _copy_from(self, x: 'TrainableBase') -> None:
        pass


class CompositionalTrainableBase(TrainableBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._components = None  # type: List[T]

    @property
    def is_trained(self):
        return self.components and all(c.is_trained for c in self.components)

    @property
    def components(self) -> Union[List[T], Dict[str, T]]:
        return self._components

    @property
    def is_pipeline(self):
        return isinstance(self.components, list)

    @components.setter
    def components(self, comps: Callable[[], Union[list, dict]]):
        if not callable(comps):
            raise TypeError('components must be a callable function that returns '
                            'a List[BaseEncoder]')
        if not getattr(self, 'init_from_yaml', False):
            self._components = comps()
        else:
            self.logger.info('components is omitted from construction, '
                             'as it is initialized from yaml config')

    def close(self):
        super().close()
        # pipeline
        if isinstance(self.components, list):
            for be in self.components:
                be.close()
        # no typology
        elif isinstance(self.components, dict):
            for be in self.components.values():
                be.close()
        elif self.components is None:
            pass
        else:
            raise TypeError('components must be dict or list, received %s' % type(self.components))

    def _copy_from(self, x: T):
        if isinstance(self.components, list):
            for be1, be2 in zip(self.components, x.components):
                be1._copy_from(be2)
        elif isinstance(self.components, dict):
            for k, v in self.components.items():
                v._copy_from(x.components[k])
        else:
            raise TypeError('components must be dict or list, received %s' % type(self.components))

    @classmethod
    def to_yaml(cls, representer, data):
        tmp = super()._dump_instance_to_yaml(data)
        tmp['components'] = data.components
        return representer.represent_mapping('!' + cls.__name__, tmp)

    @classmethod
    def from_yaml(cls, constructor, node):
        obj, data, from_dump = super()._get_instance_from_yaml(constructor, node)
        if not from_dump and 'components' in data:
            obj.components = lambda: data['components']
        return obj


def _expand_env_var(v: str) -> str:
    if isinstance(v, str):
        return parse_arg(os.path.expandvars(v))
    else:
        return v
