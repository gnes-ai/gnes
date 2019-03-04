from ..base import TrainableBase as TB


class BaseEncoder(TB):
    @TB._timeit
    def encode(self, *args, **kwargs):
        pass

    @TB._timeit
    def train(self, *args, **kwargs):
        pass


class BaseBinaryEncoder(BaseEncoder):
    @TB._timeit
    def encode(self, *args, **kwargs) -> bytes: pass
