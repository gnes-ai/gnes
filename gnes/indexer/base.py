from typing import List, Tuple, Any, Iterator, Dict, Union, Callable

from ..base import *
from ..document import BaseDocument


class BaseIndexer(TrainableBase):
    def add(self, *args, **kwargs): pass

    def query(self, *args, **kwargs) -> List[List[Tuple[Any, float]]]: pass

    def close(self):
        super().close()


class BaseBinaryIndexer(BaseIndexer):
    def __init__(self):
        super().__init__()

    def add(self, vectors: bytes, doc_ids: bytes):
        pass

    def query(self, keys: bytes, top_k: int) -> List[List[Tuple[int, float]]]:
        pass


class BaseTextIndexer(BaseIndexer):
    def add(self, docs: Iterator[BaseDocument]): pass

    def query(self, keys: List[int]) -> List[Any]: pass


class CompositionalIndexer(BaseIndexer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._component = None  # type: List['BaseIndexer']

    @property
    def component(self) -> Union[List['BaseIndexer'], Dict[str, 'BaseIndexer']]:
        return self._component

    @property
    def is_pipeline(self):
        return isinstance(self.component, list)

    @component.setter
    def component(self, comps: Callable[[], Union[list, dict]]):
        if not callable(comps):
            raise TypeError('component mus be a callable function that returns '
                            'a List[BaseIndexer]')
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
