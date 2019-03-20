from typing import List, Tuple

import numpy as np
from hnsw_cpy import HnswIndex

from ..helper import touch_dir, profiling
from .base import BaseBinaryIndexer



class HnswIndexer(BaseBinaryIndexer):
    def __init__(self, num_bytes: int, *args, **kwargs):
        super().__init__()
        self.num_bytes = num_bytes
        self._indexer = HnswIndex(num_bytes, **kwargs)

    @property
    def size(self):
        return self._indexer.size

    def add(self, vectors: bytes, doc_ids: List[int]):
        if len(vectors) % len(doc_ids) != 0:
            raise ValueError("vectors bytes should be divided by doc_ids")

        if self.num_bytes != int(len(vectors) / len(doc_ids)):
            raise ValueError("vectors bytes should be divided by doc_ids")

        offset = 0
        for doc_id in doc_ids:
            vector = vectors[offset:offset + self.num_bytes]
            self._indexer.index(doc_id, vector)
            offset += self.num_bytes

    def query(self, keys: bytes, top_k: int) -> List[List[Tuple[int, float]]]:
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
        _indexer = HnswIndex.load(load_path)
        hnsw = HnswIndexer(num_bytes=idx.num_bytes)
        hnsw._indexer = _indexer
        return hnsw
