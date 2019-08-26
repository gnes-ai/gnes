from typing import Tuple

import numpy as np

from ..base import BaseNumericEncoder


class PoolingEncoder(BaseNumericEncoder):
    def __init__(self, pooling_strategy: str = 'REDUCE_MEAN',
                 backend: str = 'numpy',
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        valid_poolings = {'REDUCE_MEAN', 'REDUCE_MAX', 'REDUCE_MEAN_MAX'}
        valid_backends = {'tensorflow', 'numpy', 'pytorch'}

        if pooling_strategy not in valid_poolings:
            raise ValueError('"pooling_strategy" must be one of %s' % valid_poolings)
        if backend not in valid_backends:
            raise ValueError('"backend" must be one of %s' % valid_backends)
        self.pooling_strategy = pooling_strategy
        self.backend = backend

    def mul_mask(self, x, m):
        if self.backend == 'pytorch':
            import torch
            return torch.mul(x, m.unsqueeze(2))
        elif self.backend == 'tensorflow':
            import tensorflow as tf
            return x * tf.expand_dims(m, axis=-1)
        elif self.backend == 'numpy':
            return 0

    def minus_mask(self, x, m, offset: int = 1e30):
        if self.backend == 'pytorch':
            return x - (1.0 - m).unsqueeze(2) * offset
        elif self.backend == 'tensorflow':
            import tensorflow as tf
            return x - tf.expand_dims(1.0 - m, axis=-1) * offset
        elif self.backend == 'numpy':
            return 0

    def masked_reduce_mean(self, x, m, jitter: float = 1e-10):
        if self.backend == 'pytorch':
            import torch
            return torch.div(torch.sum(self.mul_mask(x, m), dim=1),
                             torch.sum(m.unsqueeze(2), dim=1) + jitter)
        elif self.backend == 'tensorflow':
            import tensorflow as tf
            return tf.reduce_sum(self.mul_mask(x, m), axis=1) / (tf.reduce_sum(m, axis=1, keepdims=True) + jitter)
        elif self.backend == 'numpy':
            return np.sum(self.mul_mask(x, m), axis=1) / (np.sum(m, axis=1, keepdims=True) + jitter)

    def masked_reduce_max(self, x, m):
        if self.backend == 'pytorch':
            import torch
            return torch.max(self.minus_mask(x, m), 1)[0]
        elif self.backend == 'tensorflow':
            import tensorflow as tf
            return tf.reduce_max(self.minus_mask(x, m), axis=1)
        elif self.backend == 'numpy':
            return np.max(self.minus_mask(x, m), axis=1)

    def encode(self, data: Tuple, *args, **kwargs):
        seq_tensor, mask_tensor = data

        if self.pooling_strategy == 'REDUCE_MEAN':
            return self.masked_reduce_mean(seq_tensor, mask_tensor)
        elif self.pooling_strategy == 'REDUCE_MAX':
            return self.masked_reduce_max(seq_tensor, mask_tensor)
        elif self.pooling_strategy == 'REDUCE_MEAN_MAX':
            if self.backend == 'torch':
                import torch
                return torch.cat((self.masked_reduce_mean(seq_tensor, mask_tensor),
                                  self.masked_reduce_max(seq_tensor, mask_tensor)), dim=1)
            elif self.backend == 'tensorflow':
                import tensorflow as tf
                return tf.concat([self.masked_reduce_mean(seq_tensor, mask_tensor),
                                  self.masked_reduce_max(seq_tensor, mask_tensor)], axis=1)
            elif self.backend == 'numpy':
                return np.concatenate([self.masked_reduce_mean(seq_tensor, mask_tensor),
                                       self.masked_reduce_max(seq_tensor, mask_tensor)], axis=1)
