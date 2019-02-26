#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np

from .helpers import ploads, pdumps
from .pca import PCAMix
from .pq import PQ


class LOPQ:
    def __init__(self, k: int, m: int, num_clusters: int):
        self.k = k
        self.m = m
        self.num_clusters = num_clusters
        self.nbytes = int(k / m)
        self._check_valid()

        self.pca = PCAMix(dim_per_byte=m, num_components=k)
        self.pq = PQ(k, m, num_clusters)

    def _check_valid(self):
        assert self.k % self.m == 0, 'k % m == 0'
        assert self.num_clusters <= 255, 'cluster number error'

    def _check_vecs(self, vecs: np.ndarray):
        assert type(vecs) == np.ndarray, 'vecs type error'
        assert len(vecs.shape) == 2, 'vecs should be matrix'
        assert vecs.dtype == np.float32, 'vecs dtype np.float32!'
        assert vecs.shape[1] >= self.k, 'dimension error'

    def train(self, vecs: np.ndarray, save_path=None, pred_path=None):
        self._check_vecs(vecs)
        self.pca.train(vecs)
        vecs_new = self.pca.transform(vecs)

        if pred_path:
            self.pq.fit(vecs_new, pred_path=pred_path)
        else:
            self.pq.fit(vecs_new)

        if save_path:
            self.save(save_path)

    def transform_batch(self, vecs, data_path=None):
        vecs_new = self.pca.transform(vecs)
        return self.pq.transform_batch(vecs_new, data_path=data_path)

    def transform_single(self, vec):
        vec_new = self.pca.transform(vec)
        return self.pq.transform_single(vec_new)

    def save(self, save_path: str):
        pdumps([self.pca.mean,
                self.pca.components,
                self.pq.centroids], save_path)

    def load(self, save_path: str):
        self.pca.mean, self.pca.components, self.pq.centroids = ploads(save_path)
