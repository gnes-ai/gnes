#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np

from . import BaseEncoder as BE
from .helpers import ploads, pdumps
from .pca import PCAMixEncoder
from .pq import PQEncoder


class LOPQEncoder(BE):
    def __init__(self, k: int, m: int, num_clusters: int, model_path=None):
        super().__init__(model_path)
        self.k = k
        self.m = m
        self.num_clusters = num_clusters
        self.nbytes = int(k / m)
        self._check_valid()

        self.pca = PCAMixEncoder(dim_per_byte=m, num_components=k)
        self.pq = PQEncoder(k, m, num_clusters)

    def _check_valid(self):
        assert self.k % self.m == 0, 'k % m == 0'
        assert self.num_clusters <= 255, 'cluster number error'

    def _check_vecs(self, vecs: np.ndarray):
        assert type(vecs) == np.ndarray, 'vecs type error'
        assert len(vecs.shape) == 2, 'vecs should be matrix'
        assert vecs.dtype == np.float32, 'vecs dtype np.float32!'
        assert vecs.shape[1] >= self.k, 'dimension error'

    @BE.as_train_func
    def train(self, vecs: np.ndarray, **kwargs):
        self._check_vecs(vecs)
        self.pca.train(vecs)
        self.pq.train(self.pca.encode(vecs, **kwargs))

    @BE.train_required
    def encode(self, vecs, **kwargs) -> bytes:
        vecs_new = self.pca.encode(vecs, **kwargs)
        return self.pq.encode(vecs_new, **kwargs)

    def save(self):
        pdumps([self.pca.mean, self.pca.components, self.pq.centroids], self.model_path)

    def load(self, save_path: str):
        self.pca.mean, self.pca.components, self.pq.centroids = ploads(save_path)
