#  Tencent is pleased to support the open source community by making GNES available.
#
#  Copyright (C) 2019 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os
from typing import Tuple

import numpy as np

from ..base import BaseNumericEncoder
from ...helper import as_numpy_array


class PoolingEncoder(BaseNumericEncoder):
    def __init__(self, pooling_strategy: str = 'REDUCE_MEAN',
                 backend: str = 'numpy',
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        valid_poolings = {'REDUCE_MEAN', 'REDUCE_MAX', 'REDUCE_MEAN_MAX'}
        valid_backends = {'tensorflow', 'numpy', 'pytorch', 'torch'}

        if pooling_strategy not in valid_poolings:
            raise ValueError('"pooling_strategy" must be one of %s' % valid_poolings)
        if backend not in valid_backends:
            raise ValueError('"backend" must be one of %s' % valid_backends)
        self.pooling_strategy = pooling_strategy
        self.backend = backend

    def post_init(self):
        if self.backend in {'pytorch', 'torch'}:
            import torch
            self.torch = torch
        elif self.backend == 'tensorflow':
            os.environ['CUDA_VISIBLE_DEVICES'] = '0' if self.on_gpu else '-1'
            import tensorflow as tf
            self._tf_graph = tf.Graph()
            config = tf.ConfigProto(device_count={'GPU': 1 if self.on_gpu else 0})
            config.gpu_options.allow_growth = True
            config.log_device_placement = False
            self._sess = tf.Session(graph=self._tf_graph, config=config)
            self.tf = tf

    def mul_mask(self, x, m):
        if self.backend in {'pytorch', 'torch'}:
            return self.torch.mul(x, m.unsqueeze(2))
        elif self.backend == 'tensorflow':
            with self._tf_graph.as_default():
                return x * self.tf.expand_dims(m, axis=-1)
        elif self.backend == 'numpy':
            return x * np.expand_dims(m, axis=-1)

    def minus_mask(self, x, m, offset: int = 1e30):
        if self.backend in {'pytorch', 'torch'}:
            return x - (1.0 - m).unsqueeze(2) * offset
        elif self.backend == 'tensorflow':
            with self._tf_graph.as_default():
                return x - self.tf.expand_dims(1.0 - m, axis=-1) * offset
        elif self.backend == 'numpy':
            return x - np.expand_dims(1.0 - m, axis=-1) * offset

    def masked_reduce_mean(self, x, m, jitter: float = 1e-10):
        if self.backend in {'pytorch', 'torch'}:
            return self.torch.div(self.torch.sum(self.mul_mask(x, m), dim=1),
                                  self.torch.sum(m.unsqueeze(2), dim=1) + jitter)
        elif self.backend == 'tensorflow':
            with self._tf_graph.as_default():
                return self.tf.reduce_sum(self.mul_mask(x, m), axis=1) / (
                        self.tf.reduce_sum(m, axis=1, keepdims=True) + jitter)
        elif self.backend == 'numpy':
            return np.sum(self.mul_mask(x, m), axis=1) / (np.sum(m, axis=1, keepdims=True) + jitter)

    def masked_reduce_max(self, x, m):
        if self.backend in {'pytorch', 'torch'}:
            return self.torch.max(self.minus_mask(x, m), 1)[0]
        elif self.backend == 'tensorflow':
            with self._tf_graph.as_default():
                return self.tf.reduce_max(self.minus_mask(x, m), axis=1)
        elif self.backend == 'numpy':
            return np.max(self.minus_mask(x, m), axis=1)

    @as_numpy_array
    def encode(self, data: Tuple, *args, **kwargs):
        seq_tensor, mask_tensor = data

        if self.pooling_strategy == 'REDUCE_MEAN':
            r = self.masked_reduce_mean(seq_tensor, mask_tensor)
        elif self.pooling_strategy == 'REDUCE_MAX':
            r = self.masked_reduce_max(seq_tensor, mask_tensor)
        elif self.pooling_strategy == 'REDUCE_MEAN_MAX':
            if self.backend in {'pytorch', 'torch'}:
                r = self.torch.cat((self.masked_reduce_mean(seq_tensor, mask_tensor),
                                    self.masked_reduce_max(seq_tensor, mask_tensor)), dim=1)
            elif self.backend == 'tensorflow':
                with self._tf_graph.as_default():
                    r = self.tf.concat([self.masked_reduce_mean(seq_tensor, mask_tensor),
                                        self.masked_reduce_max(seq_tensor, mask_tensor)], axis=1)
            elif self.backend == 'numpy':
                r = np.concatenate([self.masked_reduce_mean(seq_tensor, mask_tensor),
                                    self.masked_reduce_max(seq_tensor, mask_tensor)], axis=1)

        if self.backend == 'tensorflow':
            r = self._sess.run(r)
        return r
