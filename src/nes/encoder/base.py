from typing import List, Any, Union, Dict, Callable

import numpy as np

from ..base import TrainableBase as TB


class BaseEncoder(TB):
    @TB._train_required
    def encode(self, data: Any, *args, **kwargs) -> Any:
        pass

    def _copy_from(self, x: 'BaseEncoder') -> None:
        pass


class BinaryEncoder(BaseEncoder):
    def encode(self, data: np.ndarray, *args, **kwargs) -> bytes:
        if data.dtype != np.uint8:
            raise ValueError('data must be np.uint8 but received %s' % data.dtype)
        return data.tobytes()


class CompositionalEncoder(BaseEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._component = None  # type: List['BaseEncoder']

    @property
    def component(self) -> Union[List['BaseEncoder'], Dict[str, 'BaseEncoder']]:
        return self._component

    @property
    def is_pipeline(self):
        return isinstance(self.component, list)

    @component.setter
    def component(self, comps: Callable[[], Union[list, dict]]):
        if not callable(comps):
            raise TypeError('component mus be a callable function that returns '
                            'a List[BaseEncoder]')
        if not getattr(self, 'init_from_yaml', False):
            self._component = comps()
        else:
            self.logger.info('component is omitted from construction, '
                             'as it is initialized from yaml config')

    def close(self):
        super().close()
        # pipeline
        if isinstance(self.component, list):
            for be in self.component:
                be.close()
        # no typology
        elif isinstance(self.component, dict):
            for be in self.component.values():
                be.close()
        elif self.component is None:
            pass
        else:
            raise TypeError('component must be dict or list, received %s' % type(self.component))

    def _copy_from(self, x: 'CompositionalEncoder'):
        if isinstance(self.component, list):
            for be1, be2 in zip(self.component, x.component):
                be1._copy_from(be2)
        elif isinstance(self.component, dict):
            for k, v in self.component.items():
                v._copy_from(x.component[k])
        else:
            raise TypeError('component must be dict or list, received %s' % type(self.component))

    @classmethod
    def to_yaml(cls, representer, data):
        tmp = super()._dump_instance_to_yaml(data)
        tmp['component'] = data.component
        return representer.represent_mapping('!' + cls.__name__, tmp)

    @classmethod
    def from_yaml(cls, constructor, node):
        obj, data = super()._get_instance_from_yaml(constructor, node)
        if 'component' in data:
            obj._component = data['component']
        return obj


class PipelineEncoder(CompositionalEncoder):
    @TB._train_required
    def encode(self, data: Any, *args, **kwargs) -> Any:
        if not self.component:
            raise NotImplementedError
        for be in self.component:
            data = be.encode(data, *args, **kwargs)
        return data

    def train(self, data, *args, **kwargs):
        if not self.component:
            raise NotImplementedError
        for idx, be in enumerate(self.component):
            be.train(data, *args, **kwargs)
            if idx + 1 < len(self.component):
                data = be.encode(data, *args, **kwargs)
