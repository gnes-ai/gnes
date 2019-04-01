from typing import List

import numpy as np

from .cython import IndexCore
from ..numpyindexer import NumpyIndexer


class BIndexer(NumpyIndexer):
    def __init__(self, num_bytes: int = None, *args, **kwargs):
        # super init will outut: self._vectors, self._doc_ids
        super().__init__(num_bytes, *args, **kwargs)
        self.bindexer = IndexCore(num_bytes, 4)

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

        # no return for empty result
        q_idx, d_idx = self.bindexer.find_batch_trie(keys, num_rows)
        result = [[] for _ in range(num_rows)]
        for (q, d) in zip(q_idx, d_idx):
            result[q].append(d)
        return result

    def __getstate__(self):
        d = super().__getstate__()
        del d['bindexer']
        return d

    def __setstate__(self, d):
        super().__setstate__(d)
        self.bindexer = IndexCore(self.num_bytes, 4)
        self.bindexer.index_trie(self._vectors.tobytes(),
                                 len(self._doc_ids),
                                 self._doc_ids.astype(np.uint32).tobytes())

    def close(self):
        super().close()
        self.bindexer.destroy()
