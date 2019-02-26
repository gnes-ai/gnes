#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .pq import PQ
from .pca import PCA_Mix
import numpy as np
from .helpers import ploads, pdumps


class LOPQ:
    def __init__(self, k, m, num_clusters):
        self.k = k
        self.m = m
        self.num_clusters = num_clusters
        self.nbytes = int(k/m)

        self.pca = PCA_Mix(m=m, top_n=k)
        self.pq = PQ(k, m, num_clusters)
        self._check_valid()

    def _check_valid(self):
        assert self.k % self.m == 0, "k % m == 0"
        assert self.num_clusters <= 255, "cluster number error"

    def _check_vecs(self, vecs):
        assert type(vecs) == np.ndarray, "vecs type error"
        assert len(vecs.shape) == 2, "vecs should be matrix"
        assert vecs.dtype == np.float32, "vecs dtype np.float32!"
        assert vecs.shape[1] >= self.k, "dimension error"

    def train(self, vecs, save_path=None, pred_path=None):
        self._check_vecs(vecs)
        self.pca.train(vecs)
        vecs_new = self.pca.trans(vecs)

        if pred_path:
            self.pq.fit(vecs_new, pred_path=pred_path)
        else:
            self.pq.fit(vecs_new)

        if save_path:
            self.save(save_path)

    def trans_batch(self, vecs, data_path=None):
        vecs_new = self.pca.trans(vecs)
        return self.pq.trans_batch(vecs_new, data_path=data_path)

    def trans_single(self, vec):
        vec_new = self.pca.trans(vec)
        return self.pq.trans_single(vec_new)

    def save(self, save_path):
        pdumps([self.pca.mean,
                self.pca.components,
                self.pq.centroids], save_path)

    def load(self, save_path):
        self.pca.mean, self.pca.components, self.pq.centroids = ploads(save_path)
