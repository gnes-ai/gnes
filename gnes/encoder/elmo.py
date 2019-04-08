from typing import List

import torch
import numpy as np

from ..helper import batching, cn_tokenizer

from .base import BaseEncoder, CompositionalEncoder
from elmoformanylangs import Embedder


class ElmoEncoder(BaseEncoder):
    store_args_kwargs = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        model_dir = kwargs.get('model_dir', None)
        if model_dir is None:
            raise ValueError('model_dir argument is not specified!')
        self.model_dir = model_dir

        config_path = kwargs.get('config_path', None)
        if config_path is None:
            raise ValueError('config_path is not specified!')

        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.batch_size = kwargs.get('batch_size', 64)
        self.pooling_layer = kwargs.get('pooling_layer', -1)
        if self.pooling_layer > 2:
            raise ValueError('pooling_layer = %d is not supported now!'
                                     % self.pooling_layer)
        self.pooling_strategy = kwargs.get('pooling_strategy', None)

        self._elmo = Embedder(model_dir=self.model_dir, batch_size=self.batch_size)

        self.is_trained = True
        self._encoder_args = args
        self._encoder_kwargs = kwargs

    @batching
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        # tokenize text
        batch_tokens = []
        for sent in text:
            batch_tokens.append(cn_tokenizer.tokenize(sent))

        elmo_encodes = self._elmo.sents2elmo(batch_tokens, output_layer=-2)

        pooled_data = []
        for token_encodes in elmo_encodes:
            _layer_data = None
            if self.pooling_layer == -1:
                _layer_data = np.average(token_encodes, axis=0)
            elif self.pooling_layer >= 0:
                _layer_data = token_encodes[self.pooling_layer]
            else:
                raise ValueError('pooling_layer = %d is not supported now!'
                                     % self.pooling_layer)

            _pooled_data = None
            if self.pooling_strategy is None or self.pooling_strategy == 'NONE':
                _pooled_data = payload
            elif self.pooling_strategy == 'REDUCE_MEAN':
                _pooled_data = np.mean(payload, axis=0)
            elif self.pooling_strategy == 'REDUCE_MAX':
                _pooled_data = np.amax(payload, axis=0)
            elif self.pooling_strategy == 'REDUCE_MEAN_MAX':
                _pooled_data = np.concatenate(
                    (np.mean(payload, axis=0), np.amax(payload, axis=0)),
                    axis=1)
            else:
                raise ValueError(
                    'pooling_strategy: %s has not been implemented' %
                    self.pooling_strategy)
            pooled_data.append(_pooled_data)
        return pooled_data


    def __getstate__(self):
        d = super().__getstate__()
        del d['_elmo']
        return d

    def __setstate__(self, d):
        super().__setstate__(d)
        self._elmo = Embedder(model_dir=self.model_dir, batch_size=self.batch_size)

    def close(self):
        super().close()