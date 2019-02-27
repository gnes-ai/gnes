#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np

from . import BaseEncoder as BE
from .pca import PCAMixEncoder


class LOPQEncoder(BE):
    def __init__(self, k: int, m: int, num_clusters: int, backend='numpy'):
        super().__init__()
        self.k = k
        self.m = m
        self.num_clusters = num_clusters
        self.nbytes = int(k / m)
        self._check_valid()

        self.pca = PCAMixEncoder(dim_per_byte=m, num_components=k)
        if backend == 'tensorflow':
            from .tf_pq import TFPQEncoder
            self.pq = TFPQEncoder(k, m, num_clusters)
        elif backend == 'numpy':
            from .pq import PQEncoder
            self.pq = PQEncoder(k, m, num_clusters)
        else:
            raise NotImplementedError('backend=%s is not implemented yet!' % backend)

    def _check_valid(self):
        assert self.k % self.m == 0, 'k % m == 0'
        assert self.num_clusters <= 255, 'cluster number error'

    def _check_vecs(self, vecs: np.ndarray):
        assert type(vecs) == np.ndarray, 'vecs type error'
        assert len(vecs.shape) == 2, 'vecs should be matrix'
        assert vecs.dtype == np.float32, 'vecs dtype np.float32!'
        assert vecs.shape[1] >= self.k, 'dimension error'

    @BE.as_train_func
    def train(self, vecs: np.ndarray):
        self._check_vecs(vecs)
        self.pca.train(vecs)
        vecs1 = self.pca.encode(vecs)
        self.pq.train(vecs1)

    @BE.train_required
    def encode(self, vecs, **kwargs) -> bytes:
        vecs1 = self.pca.encode(vecs)
        return self.pq.encode(vecs1, **kwargs)
