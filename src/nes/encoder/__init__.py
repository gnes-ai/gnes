from typing import List, Any

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


class PipelineEncoder(BaseEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pipeline = []  # type: List['BaseEncoder']

    @TB._train_required
    def encode(self, data: Any, *args, **kwargs) -> Any:
        if not self.pipeline:
            raise NotImplementedError
        for be in self.pipeline:
            data = be.encode(data, *args, **kwargs)
        return data

    def train(self, data, *args, **kwargs):
        if not self.pipeline:
            raise NotImplementedError
        for idx, be in enumerate(self.pipeline):
            be.train(data, *args, **kwargs)
            if idx + 1 < len(self.pipeline):
                data = be.encode(data, *args, **kwargs)

    def close(self):
        super().close()
        for be in self.pipeline:
            be.close()

    def _copy_from(self, x: 'PipelineEncoder'):
        for be1, be2 in zip(self.pipeline, x.pipeline):
            be1._copy_from(be2)

    @classmethod
    def to_yaml(cls, representer, data):
        tmp = super()._dump_instance_to_yaml(data)
        tmp.update({'pipeline': data.pipeline})
        return representer.represent_mapping('!' + cls.__name__, tmp)

    @classmethod
    def from_yaml(cls, constructor, node):
        obj, data = super()._get_instance_from_yaml(constructor, node)
        if 'pipeline' in data:
            obj.pipeline = data['pipeline']
        return obj
