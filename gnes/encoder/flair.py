from typing import List

import numpy as np
import torch
from flair.data import Sentence
from flair.embeddings import FlairEmbeddings

from .base import BaseEncoder
from ..helper import batching


class FlairEncoder(BaseEncoder):

    def __init__(self, model_name: str = 'multi-forward-fast',
                 batch_size: int = 64,
                 pooling_strategy: str = 'REDUCE_MEAN', *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model_name = model_name

        self.batch_size = batch_size
        self.pooling_strategy = pooling_strategy

        self._flair = FlairEmbeddings(self.model_name)
        self.is_trained = True

    @batching
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        # tokenize text
        batch_tokens = [Sentence(sent) for sent in text]

        flair_encodes = self._flair.embed(batch_tokens)

        pooled_data = []
        for sentence in flair_encodes:
            _layer_data = torch.stack([s.embedding for s in sentence])
            if self.pooling_strategy is None or self.pooling_strategy == 'NONE':
                _pooled_data = _layer_data
            elif self.pooling_strategy == 'REDUCE_MEAN':
                _pooled_data = torch.mean(_layer_data, 0)
            elif self.pooling_strategy == 'REDUCE_MAX':
                _pooled_data = torch.max(_layer_data, 0)[0]
            elif self.pooling_strategy == 'REDUCE_MEAN_MAX':
                _pooled_data = torch.cat(
                    (torch.mean(_layer_data, 0), torch.max(_layer_data, 0)[0]), 0)
            else:
                raise ValueError(
                    'pooling_strategy: %s has not been implemented' %
                    self.pooling_strategy)
            pooled_data.append(_pooled_data)
        return np.asarray(torch.stack(pooled_data), dtype=np.float32)

    def __getstate__(self):
        d = super().__getstate__()
        del d['_flair']
        return d

    def __setstate__(self, d):
        super().__setstate__(d)
        self._flair = FlairEmbeddings(self.model_name)
