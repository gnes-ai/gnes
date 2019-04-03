from typing import List

import torch
import numpy as np

from .base import BaseEncoder, CompositionalEncoder
from ..helper import batching


class ElmoEncoder(BaseEncoder):
    store_args_kwargs = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: load Elmo model
        self.elmo_encoder = NULL
        self.is_trained = True
        self._encoder_args = args
        self._encoder_kwargs = kwargs

    @batching
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        return self.elmo_encoder.encode(text, *args, **kwargs)  # type: np.ndarray

    def __getstate__(self):
        d = super().__getstate__()
        del d['elmo_encoder']
        return d

    def __setstate__(self, d):
        super().__setstate__(d)
        # TODO: ...
        self.elmo_encoder = NULL

    def close(self):
        self.elmo_encoder.close()