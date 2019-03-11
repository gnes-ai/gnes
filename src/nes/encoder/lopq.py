#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from . import BaseEncoder
from .pca import PCALocalEncoder

_pq_backend = os.environ.get('PQ_BACKEND', 'numpy')

if _pq_backend == 'numpy':
    from .pq import PQEncoder
elif _pq_backend == 'tensorflow':
    from .tf_pq import TFPQEncoder as PQEncoder
else:
    raise NotImplementedError('pq_backend=%s is not implemented yet!' % _pq_backend)


class LOPQEncoder(BaseEncoder):
    def __init__(self, num_bytes: int,
                 pca_output_dim: int,
                 cluster_per_byte: int = 255,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pipeline = [PCALocalEncoder(pca_output_dim, num_locals=num_bytes),
                         PQEncoder(num_bytes, cluster_per_byte)]

    def copy_from(self, x: 'LOPQEncoder'):
        super().copy_from(x)
        self.pq.copy_from(x.pq)
        self.pca.copy_from(x.pca)
