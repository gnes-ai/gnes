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
        if len(text) < 2048:
            return self.bc_encoder.encode(text, *args, **kwargs)  # type: np.ndarray
        else:
            dim = self.bc_encoder.encode([text[:1]], *args, **kwargs).shape[1]
            vecs = np.zeros((len(text), dim), dtype=np.float32)
            for _ in range(int(len(text) / 1024) + 1):
                if _*1024 >= len(text):
                    continue
                vec = self.bc_encoder.encode(text[_*1024:(_+1)*1024], *args, **kwargs)
                vecs[_*1024:(_+1)*1024] = vec
            return vecs

    @TB._timeit
    def train(self, text: List[str], *args, **kwargs) -> None:
        pass

    def __getstate__(self):
        d = super().__getstate__()
        del d['bc_encoder']
        return d

    def __setstate__(self, d):
        super().__setstate__(d)
        self.bc_encoder = BertClient(*self._bc_encoder_args, **self._bc_encoder_kwargs)
