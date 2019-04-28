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

from .cython.hnsw import IndexHnsw
from ..base import BaseBinaryIndexer
from ...helper import touch_dir, profiling


class HnswIndexer(BaseBinaryIndexer):
    def __init__(self, num_bytes: int, *args, **kwargs):
        super().__init__()
        self.num_bytes = num_bytes
        self._indexer = IndexHnsw(num_bytes, **kwargs)

    def add(self, doc_ids: List[int], vectors: bytes, *args, **kwargs):
        if len(vectors) % len(doc_ids) != 0:
            raise ValueError("vectors bytes should be divided by doc_ids")

        if self.num_bytes != int(len(vectors) / len(doc_ids)):
            raise ValueError("vectors bytes should be divided by doc_ids")

        offset = 0
        for doc_id in doc_ids:
            vector = vectors[offset:offset + self.num_bytes]
            self._indexer.index(doc_id, vector)
            offset += self.num_bytes

    def query(self, keys: bytes, top_k: int, *args, **kwargs) -> List[List[Tuple[int, float]]]:
        if len(keys) % self.num_bytes != 0:
            raise ValueError(
                "vectors bytes length should be divided by bytes_num")

        offset = 0
        n = len(keys)

        result = []
        while offset + self.num_bytes <= n:
            key = keys[offset:offset + self.num_bytes]
            offset += self.num_bytes
            resp = self._indexer.query(key, top_k)
            result.append([(r['id'], r['distance']) for r in resp])
        return result

    @profiling
    def dump(self, dump_path: str) -> None:
        touch_dir(dump_path)
        self._indexer.dump(dump_path)

    @staticmethod
    @profiling
    def load(load_path: str):
        hnsw = IndexHnsw(bytes_num=0)
        hnsw._indexer.load(load_path)
        hnsw.num_bytes = hnsw._indexer.num_bytes
        return hnsw

    @property
    def size(self):
        return self._indexer.size

    @property
    def shape(self):
        """
        :rtype: Tuple[int, int]
        :return: a tuple of (number of elements, number of bytes per vector) of the index
        """
        return self._indexer.size, self.num_bytes
