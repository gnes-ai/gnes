#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np

from . import BaseEncoder as BE
from .pca import PCALocalEncoder


class LOPQEncoder(BE):
    def __init__(self, num_bytes: int, cluster_per_byte: int = 255,
                 backend: str = 'numpy', pca_output_dim: int = -1):
        super().__init__()
        self.num_bytes = num_bytes
        self.pca_output_dim = pca_output_dim
        self.pca = None
        # if has PCA, then pca_output_dim >= num_bytes AND pca_output_dim % num_bytes == 0
        # if no PCA then output_dim >= num_bytes AND output_dim % num_bytes == 0

        if backend == 'numpy':
            from .pq import PQEncoder
            self.pq = PQEncoder(num_bytes, cluster_per_byte)
        elif backend == 'tensorflow':
            from .tf_pq import TFPQEncoder
            self.pq = TFPQEncoder(num_bytes, cluster_per_byte)
        else:
            raise NotImplementedError('backend=%s is not implemented yet!' % backend)

    @BE._as_train_func
    @BE._timeit
    def train(self, vecs: np.ndarray):
        vecs = self._do_pca(vecs, True)
        self.pq.train(vecs)

    @BE._train_required
    @BE._timeit
    def encode(self, vecs: np.ndarray, **kwargs) -> bytes:
        vecs = self._do_pca(vecs)
        return self.pq.encode(vecs, **kwargs)

    def _do_pca(self, vecs, is_train=False):
        num_sample, num_dim = vecs.shape
        if self.pca_output_dim > 0:
            if is_train:
                self.pca = PCALocalEncoder(self.pca_output_dim, num_locals=self.num_bytes)
                self.pca.train(vecs)
            self.logger.info(
                'PCA is enabled in the encoding pipeline (%d -> %d)' % (num_dim, self.pca_output_dim))
            vecs = self.pca.encode(vecs)
        return vecs

    def copy_from(self, x: 'LOPQEncoder'):
        self.pq.copy_from(x.pq)
        if self.pca and x.pca:
            self.pca.copy_from(x.pca)
        elif not self.pca:
            self.pca = x.pca
        self.is_trained = x.is_trained
        self.num_bytes = x.num_bytes
        self.pca_output_dim = x.pca_output_dim
