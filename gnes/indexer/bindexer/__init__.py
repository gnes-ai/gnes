from typing import List

import numpy as np

from .cython import IndexCore
from ..numpyindexer import NumpyIndexer


class BIndexer(NumpyIndexer):
    def __init__(self, num_bytes: int = None, ef: int = 20, *args, **kwargs):
        # super init will outut: self._vectors, self._doc_ids
        super().__init__(num_bytes, *args, **kwargs)
        self.ef = ef
        self.bindexer = IndexCore(num_bytes, 4, ef)

    def add(self, doc_ids: List[int], vectors: bytes, *args, **kwargs):
        if len(vectors) != len(doc_ids) * self.num_bytes:
            raise ValueError("vectors should equal to num_bytes*len(doc_ids)")

        super().add(doc_ids, vectors, *args, **kwargs)
        num_rows = len(doc_ids)

        cids = np.array(doc_ids, dtype=np.uint32).tobytes()
        self.bindexer.index_trie(vectors, num_rows, cids)

    def query(self, keys: bytes, top_k: int = 1, *args, **kwargs) -> List[List[int]]:
        if len(keys) % self.num_bytes != 0:
            raise ValueError("keys should be divided by num_bytes")

        num_rows = int(len(keys) / self.num_bytes)

        result = [[] for _ in range(num_rows)]

        # find the indexed items with same value
        q_idx, doc_ids = self.find_batch_trie(keys, num_rows)
        for (i, q) in zip(doc_ids, q_idx):
            result[q].append((i, 0))

        # search the indexed items with similary value
        doc_ids, dists, q_idx = self.bindexer.nsw_search(keys, num_rows)
        for (i, d, q) in zip(doc_ids, dists, q_idx):
            if d == 0:
                continue
            result[q].append((i, d))

        # get the top-k
        for q in range(num_rows):
            result[q] = result[q][:top_k]

        return result

    def __getstate__(self):
        d = super().__getstate__()
        del d['bindexer']
        return d

    def __setstate__(self, d):
        super().__setstate__(d)
        self.bindexer = IndexCore(self.num_bytes, 4, self.ef)
        self.bindexer.index_trie(self._vectors.tobytes(),
                                 len(self._doc_ids),
                                 self._doc_ids.astype(np.uint32).tobytes())

    def close(self):
        super().close()
        self.bindexer.destroy()
