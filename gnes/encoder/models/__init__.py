from typing import List
from ...helper import set_logger

from .base_torch import BaseTorchModel
from .hit_elmo import HitElmo


class BaseModel:
    def __init__(self, model_dir: str, *args, **kwargs):
        self.model_dir = model_dir
        self.verbose = 'verbose' in kwargs and kwargs['verbose']
        self.logger = set_logger(self.__class__.__name__, self.verbose)

    def predict(self, x: List[str], *args, **kwargs):
        raise NotImplemented

    def load_model(self, model_path: str):
        raise NotImplemented


__all__ = ['BaseModel',
           'BaseTorchModel',
           'HitElmo']
