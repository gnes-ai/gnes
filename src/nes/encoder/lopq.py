#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np

from src.nes.encoder.pca import PCALocalEncoder
from . import BaseEncoder as BE


class LOPQEncoder(BE):
    def __init__(self, num_bytes: int, cluster_per_byte: int = 255,
                 backend: str = 'numpy', pca_output_dim: int = -1):
        super().__init__()
        self.num_bytes = num_bytes
        self.pca_output_dim = pca_output_dim
        self.pca = None
        if pca_output_dim > 0:
            assert pca_output_dim >= num_bytes and pca_output_dim % num_bytes == 0, \
                'pca_output_dim should >= num_bytes and can be divided by num_bytes!'

        if backend == 'numpy':
            from .pq import PQEncoder
            self.pq = PQEncoder(num_bytes, cluster_per_byte)
        elif backend == 'tensorflow':
            from .tf_pq import TFPQEncoder
            self.pq = TFPQEncoder(num_bytes, cluster_per_byte)
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
        if self.pca_output_dim > 0 and vecs.shape[1] < self.pca_output_dim:
            if is_train:
                self.logger.info(
                    'PCA is enabled in the encoding pipeline (%d -> %d)' % (vecs.shape[1], self.pca_output_dim))
                self.pca = PCALocalEncoder(self.pca_output_dim, num_locals=self.num_bytes)
                self.pca.train(vecs)
            vecs = self.pca.encode(vecs)
        elif self.pca_output_dim > 0:
            self.logger.warning('PCA is enabled but incoming data has dimension of %d < %d, '
                                'no PCA needed!' % (vecs.shape[1], self.pca_output_dim))
        return vecs

    def copy_from(self, x: 'LOPQEncoder'):
        self.pq.copy_from(x.pq)
        if self.pca:
            self.pca.copy_from(x.pca)
        self.is_trained = x.is_trained
        self.num_bytes = x.num_bytes
        self.pca_output_dim = x.pca_output_dim
