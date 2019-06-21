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

from ..base import BaseNumericEncoder
from ...helper import batching, train_required


class HashEncoder(BaseNumericEncoder):
    def __init__(self, num_bytes: int,
                 num_bits: int = 8,
                 num_idx: int = 3,
                 kmeans_clusters: int = 100,
                 method: str = 'product_uniform',
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert 1 <= num_bits <= 8, 'maximum 8 hash functions in a byte'
        self.num_bytes = num_bytes
        self.num_bits = num_bits
        self.num_idx = num_idx
        self.kmeans_clusters = kmeans_clusters
        self.method = method
        self.centroids = None
        self.x = None
        self.vec_dim = None
        self.hash_cores = None
        self.mean = None
        self.var = None

    def train(self, vecs: np.ndarray, *args, **kwargs):
        self.vec_dim = vecs.shape[1]
        self.centroids = [self.train_kmeans(vecs) for _ in range(self.num_idx)]
        self.centroids = np.reshape(
            self.centroids, [1, self.num_idx, self.kmeans_clusters, self.vec_dim]).astype(np.float32)

        if self.vec_dim % self.num_bytes != 0:
            raise ValueError('vec dim should be divided by x')
        self.x = int(self.vec_dim / self.num_bytes)
        self.mean = np.mean(vecs, axis=0)
        self.var = np.var(vecs, axis=0)
        self.hash_cores = [self.ran_gen() for _ in range(self.num_bytes)]
        self.proj = np.array([2 ** i for i in range(self.num_bits)]).astype(np.int32)

    def train_kmeans(self, vecs):
        import faiss
        kmeans_instance = faiss.Kmeans(self.vec_dim,
                                       self.kmeans_clusters,
                                       niter=10)
        if vecs.dtype != np.float32:
            vecs = vecs.astype(np.float32)
        kmeans_instance.train(vecs)
        centroids = kmeans_instance.centroids
        return centroids

    def pred_kmeans(self, vecs):
        vecs = np.reshape(vecs, [vecs.shape[0], 1, 1, vecs.shape[1]])
        dist = np.sum(np.square(vecs - self.centroids), -1)
        return np.argmax(-dist, axis=-1).astype(np.uint32)

    def ran_gen(self):
        self.logger.info('hash functions with %s' % self.method)
        if self.method == 'product_uniform':
            return np.random.uniform(-1, 1, size=(self.x, self.num_bits)
                                     ).astype(np.float32)
        elif self.method == 'uniform':
            return np.random.uniform(-1, 1, size=(self.vec_dim, self.num_bits)
                                     ).astype(np.float32)
        elif self.method == 'ortho_uniform':
            from scipy.stats import ortho_group
            m = ortho_group.rvs(dim=max(self.vec_dim, self.num_bits)
                                ).astype(np.float32)
            if self.vec_dim >= self.num_bits:
                return m[:, :self.num_bits]
            else:
                return m[:self.vec_dim, :]

    def hash(self, vecs):
        ret = []
        if self.method == 'product_uniform':
            vecs = np.reshape(vecs, [vecs.shape[0], self.num_bytes, self.x])
            for i in range(self.num_bytes):
                out = np.greater(np.matmul(vecs[:, i, :], self.hash_cores[i]), 0)
                ret.append(np.sum(out * self.proj, axis=1, keepdims=1))
            return np.concatenate(ret, axis=1).astype(np.uint32)
        elif self.method == 'uniform' or self.method == 'ortho_uniform':
            for i in range(self.num_bytes):
                out = np.greater(np.matmul(vecs, self.hash_cores[i]), 0)
                ret.append(np.sum(out * self.proj, axis=1, keepdims=1))
            return np.concatenate(ret, axis=1).astype(np.uint32)

    @train_required
    @batching(batch_size=2048)
    def encode(self, vecs: np.ndarray, *args, **kwargs) -> np.ndarray:
        if vecs.shape[1] != self.vec_dim:
            raise ValueError('input dimension error')
        clusters = self.pred_kmeans(vecs)
        vecs = (vecs - self.mean) / self.var
        outcome = self.hash(vecs)
        return np.concatenate([clusters, outcome], axis=1)

    def _copy_from(self, x: 'HashEncoder') -> None:
        self.num_bytes = x.num_bytes
        self.num_bits = x.num_bits
        self.num_idx = x.num_idx
        self.kmeans_clusters = x.kmeans_clusters
        self.centroids = x.centroids
        self.method = x.method
        self.x = x.x
        self.vec_dim = x.vec_dim
        self.hash_cores = x.hash_cores
        self.mean = x.mean
        self.var = x.var
        self.is_trained = x.is_trained
