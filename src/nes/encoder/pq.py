from typing import List

import faiss
import numpy as np

from . import BaseEncoder as BE


def train_kmeans(x: np.ndarray, num_clusters: int, num_iters: int, verbose: bool) -> np.ndarray:
    kmeans = faiss.Kmeans(x.shape[1], num_clusters, num_iters, verbose)
    kmeans.train(x)
    return kmeans.centroids


class PQEncoder(BE):
    def __init__(self, num_bytes: int, cluster_per_byte: int = 255):
        super().__init__()
        assert 1 < cluster_per_byte <= 255, 'cluster number should >1 and <= 255 (0 is reserved for NOP)'
        self.num_bytes = num_bytes
        self.num_clusters = cluster_per_byte
        self.centroids = None

    def train(self, vecs: np.ndarray, num_iters: int = 20):
        dim_per_byte = self._get_dim_per_byte(vecs)

        res = []  # type: List[np.ndarray]
        for j in range(self.num_bytes):
            store = vecs[:, (dim_per_byte * j):(dim_per_byte * (j + 1))]
            store = np.array(store, dtype=np.float32)
            res.append(train_kmeans(store, num_iters=num_iters,
                                    num_clusters=self.num_clusters,
                                    verbose=self.verbose))

        self.centroids = np.expand_dims(np.array(res, dtype=np.float32), 0)

    @BE._train_required
    def encode(self, vecs: np.ndarray, **kwargs) -> bytes:
        dim_per_byte = self._get_dim_per_byte(vecs)

        x = np.reshape(vecs, [vecs.shape[0], self.num_bytes, 1, dim_per_byte])
        x = np.sum(np.square(x - self.centroids), -1)
        # start from 1
        x = np.argmax(-x, 2) + 1

        return np.array(x, dtype=np.uint8).tobytes()

    def _get_dim_per_byte(self, vecs):
        num_dim = vecs.shape[1]
        assert num_dim >= self.num_bytes and num_dim % self.num_bytes == 0, \
            'input dimension should >= num_bytes and can be divided by num_bytes!'
        return int(num_dim / self.num_bytes)

    def copy_from(self, x: 'PQEncoder') -> None:
        self.num_bytes = x.num_bytes
        self.num_clusters = x.num_clusters
        self.centroids = x.centroids
        self.is_trained = x.is_trained
