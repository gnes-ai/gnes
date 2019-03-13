from typing import List, Tuple

import numpy as np

from . import BaseBinaryIndexer


class NumpyIndexer(BaseBinaryIndexer):
    def __init__(self, num_bytes: int = None, *args, **kwargs):
        super().__init__()
        self.num_bytes = num_bytes
        self._vectors = None  # type: np.ndarray
        self._doc_ids = None  # type: np.ndarray

    def add(self, vectors: bytes, doc_ids: List[int]):
        if len(vectors) % len(doc_ids) != 0:
            raise ValueError("vectors bytes should be divided by doc_ids")

        if not self.num_bytes:
            self.num_bytes = int(len(vectors) / len(doc_ids))
        elif self.num_bytes != int(len(vectors) / len(doc_ids)):
            raise ValueError("vectors bytes should be divided by doc_ids")

        vectors = np.frombuffer(vectors, dtype=np.uint8).reshape(
            len(doc_ids), self.num_bytes)

        doc_ids = np.array(doc_ids)
        if self._vectors is not None:
            self._vectors = np.concatenate([self._vectors, vectors], axis=0)
            self._doc_ids = np.concatenate([self._doc_ids, doc_ids], axis=0)
        else:
            self._vectors = vectors
            self._doc_ids = doc_ids

    def query(self, keys: bytes, top_k: int) -> List[List[Tuple[int, float]]]:
        keys = np.frombuffer(keys, dtype=np.uint8).reshape([-1, 1, self.num_bytes])

        dist = keys - np.expand_dims(self._vectors, axis=0)
        dist = np.sum(np.minimum(np.abs(dist), 1), -1) / self.num_bytes

        ret = []
        for ids in dist:
            rk = sorted(enumerate(ids), key=lambda x: x[1])
            ret.append([(self._doc_ids[rk[i][0]].tolist(), rk[i][1]) for i in range(top_k)])

        return ret
