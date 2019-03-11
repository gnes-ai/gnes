from typing import List, Any

from ..base import TrainableBase as TB


class BaseEncoder(TB):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pipeline = []  # type: List['BaseEncoder']

    @TB._timeit
    @TB._train_required
    def encode(self, data: Any, *args, **kwargs) -> bytes:
        for be in self.pipeline:
            data = be.encode(data, *args, **kwargs)
        return super().encode(data, *args, **kwargs)

    @TB._timeit
    @TB._as_train_func
    def train(self, data, *args, **kwargs):
        for be in self.pipeline:
            be.train(data, *args, **kwargs)
            data = be.encode(data, *args, **kwargs)
        return super().train(data, *args, **kwargs)

    def close(self):
        super().close()
