from typing import List

import torch
import numpy as np

from ..helper import batching

from .base import BaseEncoder, CompositionalEncoder
from .models.hit_elmo import HitElmo


class ElmoEncoder(BaseEncoder):
    store_args_kwargs = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # model_dir = kwargs.get('model_dir', None)
        # if model_dir is None:
        #     raise ValueError('Unknown model_dir argument')

        # config_path = kwargs.get('config_path', None)

        self.elmo_encoder = HitElmo(*args, **kwargs)
        self.is_trained = True
        self._encoder_args = args
        self._encoder_kwargs = kwargs

    @batching
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        return self.elmo_encoder.predict(text, *args, **kwargs)  # type: np.ndarray

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