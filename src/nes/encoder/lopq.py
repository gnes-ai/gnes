#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import PipelineEncoder, BinaryEncoder
from .pca import PCALocalEncoder
from .pq import PQEncoder
from .tf_pq import TFPQEncoder


class LOPQEncoder(PipelineEncoder):
    def __init__(self, num_bytes: int,
                 pca_output_dim: int,
                 cluster_per_byte: int = 255,
                 pq_backend: str = 'numpy',
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        pq = {'numpy': lambda: PQEncoder(num_bytes, cluster_per_byte),
              'tensorflow': lambda: TFPQEncoder(num_bytes, cluster_per_byte)}.get(pq_backend, lambda: None)()
        if not pq:
            raise NotImplementedError('pq_backend: %s is not implemented' % pq)

        self.pipeline = [PCALocalEncoder(pca_output_dim, num_locals=num_bytes), pq,
                         BinaryEncoder()]
