from typing import List, Tuple, Union

import numpy as np

from .cython import IndexCore
from ..base import BaseBinaryIndexer


class BIndexer(BaseBinaryIndexer):
    def __init__(self, num_bytes: int = None,
                 ef: int = 20,
                 insert_iterations: int = 1000,
                 query_iterations: int = 1000,
                 data_path: str = './bindexer.bin',
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_bytes = num_bytes
        self.ef = ef
        self.insert_iterations = insert_iterations
        self.query_iterations = query_iterations
        self.data_path = data_path
        self.bindexer = IndexCore(num_bytes, 4, ef,
                                  insert_iterations,
                                  query_iterations)

    def add(self, doc_ids: List[int], vectors: bytes, *args, **kwargs):
        if len(vectors) != len(doc_ids) * self.num_bytes:
            raise ValueError("vectors should equal to num_bytes*len(doc_ids)")

        num_rows = len(doc_ids)

        cids = np.array(doc_ids, dtype=np.uint32).tobytes()
        self.bindexer.index_trie(vectors, num_rows, cids)

    def query(self, keys: bytes, top_k: int = 1, normalized_score=False, *args, **kwargs) -> List[List[Tuple[int, Union[float, int]]]]:
        if len(keys) % self.num_bytes != 0:
            raise ValueError("keys should be divided by num_bytes")

        num_rows = int(len(keys) / self.num_bytes)

        result = [[] for _ in range(num_rows)]

        # find the indexed items with same value
        q_idx, doc_ids = self.bindexer.find_batch_trie(keys, num_rows)
        for (i, q) in zip(doc_ids, q_idx):
            result[q].append((i, 1. if normalized_score else 0))

        # search the indexed items with similary value
        doc_ids, dists, q_idx = self.bindexer.nsw_search(keys, num_rows)
        for (i, d, q) in zip(doc_ids, dists, q_idx):
            if d == 0:
                continue
            result[q].append((i, (1. - d / self.num_bytes) if normalized_score else d))

        # get the top-k
        for q in range(num_rows):
            result[q] = result[q][:top_k]

        return result

    def __getstate__(self):
        self.bindexer.save(self.data_path)
        d = super().__getstate__()
        del d['bindexer']
        return d

    def __setstate__(self, d):
        super().__setstate__(d)
        self.bindexer = IndexCore(self.num_bytes, 4, self.ef,
                                  self.insert_iterations,
                                  self.query_iterations)
        self.bindexer.load(self.data_path)

    def close(self):
        self.bindexer.destroy()
