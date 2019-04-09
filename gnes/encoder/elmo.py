from typing import List

import numpy as np
from elmoformanylangs import Embedder

from .base import BaseEncoder
from ..helper import batching, cn_tokenizer


class ElmoEncoder(BaseEncoder):

    def __init__(self, model_dir: str, batch_size: int = 64, pooling_layer: int = -1,
                 pooling_strategy: str = 'REDUCE_MEAN', *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model_dir = model_dir

        self.batch_size = batch_size
        if pooling_layer > 2:
            raise ValueError('pooling_layer = %d is not supported now!' %
                             pooling_layer)
        self.pooling_layer = pooling_layer
        self.pooling_strategy = pooling_strategy

        self._elmo = Embedder(model_dir=self.model_dir, batch_size=self.batch_size)
        self.is_trained = True

    @batching
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        # tokenize text
        batch_tokens = [cn_tokenizer.tokenize(sent) for sent in text]

        elmo_encodes = self._elmo.sents2elmo(batch_tokens, output_layer=-2)

        pooled_data = []
        for token_encodes in elmo_encodes:
            if self.pooling_layer == -1:
                _layer_data = np.average(token_encodes, axis=0)
            elif self.pooling_layer >= 0:
                _layer_data = token_encodes[self.pooling_layer]
            else:
                raise ValueError('pooling_layer = %d is not supported now!' %
                                 self.pooling_layer)

            if self.pooling_strategy is None or self.pooling_strategy == 'NONE':
                _pooled_data = _layer_data
            elif self.pooling_strategy == 'REDUCE_MEAN':
                _pooled_data = np.mean(_layer_data, axis=0)
            elif self.pooling_strategy == 'REDUCE_MAX':
                _pooled_data = np.amax(_layer_data, axis=0)
            elif self.pooling_strategy == 'REDUCE_MEAN_MAX':
                _pooled_data = np.concatenate(
                    (np.mean(_layer_data, axis=0), np.amax(_layer_data, axis=0)),
                    axis=1)
            else:
                raise ValueError(
                    'pooling_strategy: %s has not been implemented' %
                    self.pooling_strategy)
            pooled_data.append(_pooled_data)
        return np.asarray(pooled_data, dtype=np.float32)

    def __getstate__(self):
        d = super().__getstate__()
        del d['_elmo']
        return d

    def __setstate__(self, d):
        super().__setstate__(d)
        self._elmo = Embedder(
            model_dir=self.model_dir, batch_size=self.batch_size)
