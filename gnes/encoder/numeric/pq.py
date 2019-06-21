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

# pylint: disable=low-comment-ratio


import numpy as np

from ..base import BaseBinaryEncoder
from ...helper import batching, train_required


class PQEncoder(BaseBinaryEncoder):
    def __init__(self, num_bytes: int, cluster_per_byte: int = 255, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert 1 < cluster_per_byte <= 255, 'cluster number should >1 and <= 255 (0 is reserved for NOP)'
        self.num_bytes = num_bytes
        self.num_clusters = cluster_per_byte
        self.centroids = None

    def train(self, vecs: np.ndarray, *args, **kwargs):
        import faiss

        dim_per_byte = self._get_dim_per_byte(vecs)

        # use faiss ProductQuantizer directly
        vecs = vecs.astype(np.float32)
        model = faiss.ProductQuantizer(vecs.shape[1], self.num_bytes, 8)
        model.ksub = self.num_clusters
        model.byte_per_idx = 1

        model.train(vecs)
        centroids = faiss.vector_to_array(model.centroids)
        centroids = centroids[: self.num_clusters * vecs.shape[1]]
        self.centroids = np.reshape(centroids, [1, self.num_bytes,
                                                self.num_clusters,
                                                dim_per_byte])

    @train_required
    @batching(batch_size=2048)
    def encode(self, vecs: np.ndarray, *args, **kwargs) -> np.ndarray:
        dim_per_byte = self._get_dim_per_byte(vecs)

        x = np.reshape(vecs, [vecs.shape[0], self.num_bytes, 1, dim_per_byte])
        x = np.sum(np.square(x - self.centroids), -1)
        # start from 1
        x = np.argmax(-x, 2) + 1

        return np.array(x, dtype=np.uint8)

    def _get_dim_per_byte(self, vecs: np.ndarray):
        num_dim = vecs.shape[1]
        assert num_dim >= self.num_bytes and num_dim % self.num_bytes == 0, \
            'input dimension (=%d) should >= num_bytes (=%d) and can be divided by num_bytes!' % (
                num_dim, self.num_bytes)
        return int(num_dim / self.num_bytes)

    def _copy_from(self, x: 'PQEncoder') -> None:
        self.num_bytes = x.num_bytes
        self.num_clusters = x.num_clusters
        self.centroids = x.centroids
        self.is_trained = x.is_trained
