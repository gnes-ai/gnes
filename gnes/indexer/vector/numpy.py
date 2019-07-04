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

from typing import List, Tuple

import numpy as np

from ..base import BaseVectorIndexer
from ..key_only import ListKeyIndexer


class NumpyIndexer(BaseVectorIndexer):

    def __init__(self, num_bytes: int = None, *args, **kwargs):
        super().__init__()
        self.num_bytes = num_bytes
        self._vectors = None  # type: np.ndarray
        self._key_info_indexer = ListKeyIndexer()

    def add(self, keys: List[Tuple[int, int]], vectors: np.ndarray, weights: List[float], *args,
            **kwargs):
        if len(vectors) % len(keys) != 0:
            raise ValueError('vectors bytes should be divided by doc_ids')

        if not self.num_bytes:
            self.num_bytes = vectors.shape[1]
        elif self.num_bytes != vectors.shape[1]:
            raise ValueError(
                "vectors' shape [%d, %d] does not match with indexer's dim: %d" %
                (vectors.shape[0], vectors.shape[1], self.num_bytes))

        if self._vectors is not None:
            self._vectors = np.concatenate([self._vectors, vectors], axis=0)
        else:
            self._vectors = vectors
        self._key_info_indexer.add(keys, weights)

    def query(self, keys: np.ndarray, top_k: int, *args, **kwargs
              ) -> List[List[Tuple]]:
        keys = np.expand_dims(keys, axis=1)
        dist = keys - np.expand_dims(self._vectors, axis=0)
        score = 1 - np.sum(np.minimum(np.abs(dist), 1), -1) / self.num_bytes

        ret = []
        for ids in score:
            rk = sorted(enumerate(ids), key=lambda x: -x[1])
            chunk_info = self._key_info_indexer.query([j[0] for j in rk])

            ret.append([(*r, s) for r, s in zip(chunk_info, [j[1] for j in rk])])
        return ret
