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
from typing import List, Tuple, Union

import numpy as np

from .cython import IndexCore
from ..base import BaseBinaryIndexer


class BIndexer(BaseBinaryIndexer):
    lock_work_dir = True

    def __init__(self, num_bytes: int = None,
                 ef: int = 20,
                 insert_iterations: int = 1000,
                 query_iterations: int = 1000,
                 data_path: str = './bindexer_data',
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_bytes = num_bytes
        self.ef = ef
        self.insert_iterations = insert_iterations
        self.query_iterations = query_iterations

        self.work_dir = data_path
        self.indexer_bin_path = os.path.join(self.work_dir, "indexer.bin")

    def _post_init(self):
        self.bindexer = IndexCore(self.num_bytes, 4, self.ef,
                                  self.insert_iterations,
                                  self.query_iterations)
        if os.path.exists(self.indexer_bin_path):
            self.bindexer.load(self.indexer_bin_path)


    def add(self, doc_ids: List[int], vectors: bytes, *args, **kwargs):
        if len(vectors) != len(doc_ids) * self.num_bytes:
            raise ValueError("vectors should equal to num_bytes*len(doc_ids)")

        num_rows = len(doc_ids)

        cids = np.array(doc_ids, dtype=np.uint32).tobytes()
        self.bindexer.index_trie(vectors, num_rows, cids)

    def query(self, keys: bytes, top_k: int = 1, normalized_score=False, method: str = 'nsw', *args, **kwargs) -> List[
        List[Tuple[int, Union[float, int]]]]:
        if len(keys) % self.num_bytes != 0:
            raise ValueError("keys should be divided by num_bytes")

        num_rows = int(len(keys) / self.num_bytes)

        result = [[] for _ in range(num_rows)]

        if method == 'nsw':
            # find the indexed items with same value
            q_idx, doc_ids = self.bindexer.find_batch_trie(keys, num_rows)
            for (i, q) in zip(doc_ids, q_idx):
                result[q].append((i, 1. if normalized_score else 0))

            # search the indexed items with similary value
            doc_ids, dists, q_idx = self.bindexer.nsw_search(keys, num_rows, top_k)
            for (i, d, q) in zip(doc_ids, dists, q_idx):
                if d == 0:
                    continue
                result[q].append((i, (1. - d / self.num_bytes) if normalized_score else d))

            # get the top-k
            for q in range(num_rows):
                result[q] = result[q][:top_k]
        elif method == 'force':
            doc_ids, dists, q_idx = self.bindexer.force_search(keys, num_rows, top_k)
            for (i, d, q) in zip(doc_ids, dists, q_idx):
                result[q].append((i, (1. - d / self.num_bytes) if normalized_score else d))

        return result

    def __getstate__(self):
        self.bindexer.save(self.indexer_bin_path)
        d = super().__getstate__()
        del d['bindexer']
        return d