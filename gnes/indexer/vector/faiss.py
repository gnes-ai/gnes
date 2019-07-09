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


import os
from typing import List, Tuple

import numpy as np

from ..base import BaseVectorIndexer
from ..key_only import ListKeyIndexer


class FaissIndexer(BaseVectorIndexer):
    lock_work_dir = True

    def __init__(self, num_dim: int, index_key: str, data_path: str, *args, **kwargs):
        super().__init__()
        self.work_dir = data_path
        self.indexer_file_path = os.path.join(self.work_dir, self.internal_index_path)
        self.num_dim = num_dim
        self.index_key = index_key
        self._key_info_indexer = ListKeyIndexer()

    def post_init(self):
        import faiss
        try:
            self._faiss_index = faiss.read_index(self.indexer_file_path)
        except RuntimeError:
            self.logger.warning('fail to load model from %s, will init an empty one' % self.indexer_file_path)
            self._faiss_index = faiss.index_factory(self.num_dim, self.index_key)

    def add(self, keys: List[Tuple[int, int]], vectors: np.ndarray, weights: List[float], *args, **kwargs):
        if len(vectors) != len(keys):
            raise ValueError("vectors length should be equal to doc_ids")

        if vectors.dtype != np.float32:
            raise ValueError("vectors should be ndarray of float32")

        self._key_info_indexer.add(keys, weights)
        self._faiss_index.add(vectors)

    def query(self, keys: np.ndarray, top_k: int, *args, **kwargs) -> List[List[Tuple]]:
        if keys.dtype != np.float32:
            raise ValueError("vectors should be ndarray of float32")

        score, ids = self._faiss_index.search(keys, top_k)
        ret = []
        for _id, _score in zip(ids, score):
            ret_i = []
            chunk_info = self._key_info_indexer.query(_id)
            for c_info, _score_i in zip(chunk_info, _score):
                ret_i.append((*c_info, -_score_i))
            ret.append(ret_i)

        return ret

    @property
    def size(self):
        return self._faiss_index.ntotal

    def __getstate__(self):
        import faiss
        d = super().__getstate__()
        faiss.write_index(self._faiss_index, self.indexer_file_path)
        return d
