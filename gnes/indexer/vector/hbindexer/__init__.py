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
from typing import List, Tuple, Any

import numpy as np

from .cython import IndexCore
from ...base import BaseVectorIndexer


class HBIndexer(BaseVectorIndexer):

    def __init__(self,
                 num_clusters: int = 100,
                 num_bytes: int = 8,
                 n_idx: int = 1,
                 data_path: str = './hbindexer_data',
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.n_bytes = num_bytes
        self.n_clusters = num_clusters
        self.n_idx = n_idx
        self.data_path = data_path
        self._weight_norm = 2 ** 16 - 1
        if self.n_idx <= 0:
            raise ValueError('There should be at least 1 clustering slot')

    def post_init(self):
        self.hbindexer = IndexCore(self.n_clusters, self.n_bytes, self.n_idx)
        try:
            if not os.path.exists(self.data_path):
                raise FileNotFoundError('"data_path" is not exist')
            if os.path.isdir(self.data_path):
                raise IsADirectoryError('"data_path" must be a file path, not a directory')
            self.hbindexer.load(self.data_path)
        except (FileNotFoundError, IsADirectoryError):
            self.logger.warning('fail to load model from %s, will create an empty one' % self.data_path)

    def add(self, keys: List[Tuple[int, Any]], vectors: np.ndarray, weights: List[float], *args, **kwargs):
        if len(vectors) != len(keys):
            raise ValueError("vectors length should be equal to doc_ids")

        if vectors.dtype != np.uint32:
            raise ValueError("vectors should be ndarray of uint32")

        n = len(keys)
        keys, offsets = zip(*keys)
        keys = np.array(keys, dtype=np.uint32).tobytes()
        offsets = np.array(offsets, dtype=np.uint16).tobytes()
        weights = np.array(weights * self._weight_norm, dtype=np.uint16).tobytes()
        clusters = vectors[:, :self.n_idx].tobytes()
        vectors = vectors[:, self.n_idx:].astype(np.uint8).tobytes()
        self.hbindexer.index_trie(vectors, clusters, keys, offsets, weights, n)

    def query(self,
              vectors: np.ndarray,
              top_k: int,
              *args,
              **kwargs) -> List[List[Tuple]]:

        if vectors.dtype != np.uint32:
            raise ValueError("vectors should be ndarray of uint32")

        # num_rows = int(len(keys) / self.num_bytes)
        n = vectors.shape[0]
        clusters = vectors[:, :self.n_idx].tobytes()
        vectors = vectors[:, self.n_idx:].astype(np.uint8).tobytes()

        result = [{} for _ in range(n)]

        doc_ids, offsets, weights, dists, q_idx = self.hbindexer.query(
            vectors, clusters, n, top_k * self.n_idx)
        for (i, o, w, d, q) in zip(doc_ids, offsets, weights, dists, q_idx):
            result[q][(i, o, w / self._weight_norm)] = self.normalize_score(d)

        return [sorted(ret.items(), key=lambda x: -x[1])[:top_k] for ret in result]

    def normalize_score(self, distance: int, *args, **kwargs) -> float:
        return 1. - distance / self.n_bytes * 8

    def __getstate__(self):
        self.hbindexer.save(self.data_path)
        d = super().__getstate__()
        return d
