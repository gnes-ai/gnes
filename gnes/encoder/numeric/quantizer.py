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


import numpy as np
from itertools import product

from ..base import BaseBinaryEncoder
from ...helper import batching


class QuantizerEncoder(BaseBinaryEncoder):
    batch_size = 2048

    def __init__(self, dim_per_byte: int, cluster_per_byte: int = 255,
                 upper_bound: int = 10000,
                 lower_bound: int = -10000,
                 divide_method: str = 'average',
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert 1 < cluster_per_byte <= 255, 'cluster number should >1 and <= 255 (0 is reserved for NOP)'
        self.dim_per_byte = dim_per_byte
        self.num_clusters = cluster_per_byte
        self.upper_bound = upper_bound
        self.lower_bound = lower_bound
        self.divide_method = divide_method
        self.centroids = None

    def train(self):
        """
        calculate centroids for quantizer
        two kinds of divide methods are supported now: average, random
        average: split the space averagely and centroids of clusters lie on the corner of sub-space
        random: randomly pick points and treat them as centroids of clusters
        Variable Explaination:
            num_sample_per_dim: number of points to be sample on each dimension
        """

        self.centroids = []
        num_sample_per_dim = np.ceil(pow(self.num_clusters, 1 / self.dim_per_byte)).astype(np.uint8)
        axis_point = []
        if self.divide_method == 'average':
            interval = (self.upper_bound - self.lower_bound) / (num_sample_per_dim + 1)
            for i in range(1, num_sample_per_dim + 1):
                axis_point.append(self.lower_bound + i * interval)
            coordinates = [axis_point for _ in range(self.dim_per_byte)]
        elif self.divide_method == 'random':
            for i in range(self.dim_per_byte):
                axis_point.append(np.random.randint(self.lower_bound, self.upper_bound,
                                                    size=[num_sample_per_dim]))
            coordinates = axis_point
        else:
            raise NotImplementedError

        for item in product(*coordinates):
            self.centroids.append(list(item))
        self.centroids = self.centroids[:self.num_clusters]

    @batching
    def encode(self, vecs: np.ndarray, *args, **kwargs) -> np.ndarray:
        num_bytes = self._get_num_bytes(vecs)

        x = np.reshape(vecs, [vecs.shape[0], num_bytes, 1, self.dim_per_byte])
        x = np.sum(np.square(x - self.centroids), -1)
        # start from 1
        x = np.argmax(-x, 2) + 1

        return np.array(x, dtype=np.uint8)

    def _get_num_bytes(self, vecs: np.ndarray):
        num_dim = vecs.shape[1]
        assert num_dim % self.dim_per_byte == 0 and num_dim >= (num_dim % self.dim_per_byte), \
            'input dimension (=%d) should be divided by dim_per_byte (=%d)!' % (
                num_dim, self.dim_per_byte)
        return int(num_dim / self.dim_per_byte)
