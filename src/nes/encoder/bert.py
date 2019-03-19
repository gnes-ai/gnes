from typing import List

import numpy as np
from bert_serving.client import BertClient

from .base import BaseEncoder
from ..helper import batching


class BertEncoder(BaseEncoder):
    store_args_kwargs = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bc_encoder = BertClient(*args, **kwargs)
        # dirty fix, should be fixed in bert-as-service
        # patch submitted, pypi updated, wait mirror to be updated
        self.bc_encoder.token_info_available = False
        self.is_trained = True
        self._bc_encoder_args = args
        self._bc_encoder_kwargs = kwargs

    @batching
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        return self.bc_encoder.encode(text, *args, **kwargs)  # type: np.ndarray

    def __getstate__(self):
        d = super().__getstate__()
        del d['bc_encoder']
        return d

    def __setstate__(self, d):
        super().__setstate__(d)
        self.bc_encoder = BertClient(*self._bc_encoder_args, **self._bc_encoder_kwargs)
