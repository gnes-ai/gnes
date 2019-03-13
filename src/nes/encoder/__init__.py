from typing import List, Any

from ..base import TrainableBase as TB


class BaseEncoder(TB):
    @TB._timeit
    @TB._train_required
    def encode(self, data: Any, *args, **kwargs) -> Any:
        pass

    def _copy_from(self, x: 'BaseEncoder') -> None:
        pass


class PipelineEncoder(BaseEncoder):
    @TB._yaml_init
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pipeline = []  # type: List['BaseEncoder']

    @TB._timeit
    @TB._train_required
    def encode(self, data: Any, *args, **kwargs) -> Any:
        if not self.pipeline:
            raise NotImplementedError
        for be in self.pipeline:
            data = be.encode(data, *args, **kwargs)
        return data

    @TB._timeit
    @TB._as_train_func
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
