from typing import List

import faiss
import numpy as np

from . import BaseEncoder as BE


def train_kmeans(x: np.ndarray, num_clusters: int, num_iter: int = 20) -> np.ndarray:
    kmeans = faiss.Kmeans(x.shape[1], num_clusters, num_iter, True)
    kmeans.train(x)
    return kmeans.centroids


class PQEncoder(BE):
    def __init__(self, k: int, m: int, num_clusters):
        super().__init__()
        self.k = k
        self.m = m
        self.num_bytes = int(k / m)
        self.num_clusters = num_clusters
        self.centroids = None

    @BE.as_train_func
    def train(self, vecs: np.ndarray):
        assert vecs.shape[1] == self.k, 'Incorrect dimension for input!'
        res = []  # type: List[np.ndarray]
        for j in range(self.num_bytes):
            store = vecs[:, (self.m * j):(self.m * (j + 1))]
            store = np.array(store, dtype=np.float32)
            res.append(train_kmeans(store, num_clusters=self.num_clusters))

        self.centroids = np.expand_dims(np.array(res, dtype=np.float32), 0)

    @BE.train_required
    def encode(self, vecs: np.ndarray) -> bytes:
        x = np.reshape(vecs, [vecs.shape[0], self.num_bytes, 1, self.m])
        x = np.sum(np.square(x - self.centroids), -1)
        # start from 1
        x = np.argmax(-x, 2) + 1

        return np.array(x, dtype=np.uint8).tobytes()
