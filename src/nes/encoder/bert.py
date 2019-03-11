from typing import List

import numpy as np
from bert_serving.client import BertClient

from . import BaseEncoder
from ..base import TrainableBase as TB


class BertEncoder(BaseEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bc_encoder = BertClient(*args, **kwargs)
        self.is_trained = True
        self._bc_encoder_args = args
        self._bc_encoder_kwargs = kwargs

    @TB._timeit
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        return self.bc_encoder.encode(text, *args, **kwargs)  # type: np.ndarray

    @TB._timeit
    def train(self, text, *args, **kwargs) -> None:
        pass

    def __getstate__(self):
        d = super().__getstate__()
        del d['bc_encoder']
        return d

    def __setstate__(self, d):
        super().__setstate__(d)
        self.bc_encoder = BertClient(*self._bc_encoder_args, **self._bc_encoder_kwargs)
