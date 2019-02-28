#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np

from . import BaseEncoder as BE
from .pca import PCALocalEncoder


class LOPQEncoder(BE):
    def __init__(self, num_bytes: int, dim_per_byte: int,
                 cluster_per_byte: int = 255,
                 backend: str = 'numpy', use_pca: bool = True):
        super().__init__()
        self.num_bytes = num_bytes

        if use_pca:
            self.pca = PCALocalEncoder(num_bytes * dim_per_byte, dim_per_byte)
        else:
            self.pca = None

        if backend == 'numpy':
            from .pq import PQEncoder
            self.pq = PQEncoder(dim_per_byte, cluster_per_byte)
        elif backend == 'tensorflow':
            from .tf_pq import TFPQEncoder
            self.pq = TFPQEncoder(dim_per_byte, cluster_per_byte)
        else:
            raise NotImplementedError('backend=%s is not implemented yet!' % backend)

    @BE._as_train_func
    def train(self, vecs: np.ndarray):
        vecs = self._do_pca(vecs, True)
        self.pq.train(vecs)

    @BE._train_required
    def encode(self, vecs: np.ndarray, **kwargs) -> bytes:
        vecs = self._do_pca(vecs)
        return self.pq.encode(vecs, **kwargs)

    def _do_pca(self, vecs, is_train=False):
        if self.pca and vecs.shape[1] < self.pca.output_dim:
            if is_train: self.pca.train(vecs)
            vecs = self.pca.encode(vecs)
        elif self.pca:
            self.logger.warning('PCA is enabled but incoming data has dimension of %d < %d, '
                                'no PCA needed!' % (vecs.shape[1], self.pca.output_dim))
        return vecs

    def copy_from(self, x: 'LOPQEncoder'):
        self.pq.copy_from(x.pq)
        self.pca.copy_from(x.pca)
        self.is_trained = x.is_trained
