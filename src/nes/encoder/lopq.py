#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np

from . import BaseEncoder
from .helpers import ploads, pdumps
from .pca import PCAMixEncoder
from .pq import PQEncoder


class LOPQEncoder(BaseEncoder):
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

    @BaseEncoder.as_pretrain
    def train(self, vecs: np.ndarray):
        self._check_vecs(vecs)
        self.pca.train(vecs)
        self.pq.train(self.pca.encode(vecs))

    @BaseEncoder.pretrain_required
    def encode(self, vecs) -> bytes:
        vecs_new = self.pca.encode(vecs)
        return self.pq.encode(vecs_new)

    @BaseEncoder.pretrain_required
    def encode_single(self, vec) -> bytes:
        vec_new = self.pca.encode(vec)
        return self.pq.encode_single(vec_new)

    def save(self):
        pdumps([self.pca.mean, self.pca.components, self.pq.centroids], self.model_path)

    def load(self, save_path: str):
        self.pca.mean, self.pca.components, self.pq.centroids = ploads(save_path)
