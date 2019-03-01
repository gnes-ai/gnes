from typing import List

from bert_serving.client import BertClient

from . import BaseEncoder as BE
from .lopq import LOPQEncoder


class BertBinaryEncoder(LOPQEncoder):
    def __init__(self, num_bytes: int = 8,
                 cluster_per_byte: int = 255,
                 backend: str = 'numpy',
                 pca_output_dim: int = 256,
                 *args, **kwargs):
        super().__init__(num_bytes, cluster_per_byte, backend, pca_output_dim)
        self.bc_encoder = BertClient(*args, **kwargs)
        self._bc_encoder_args = args
        self._bc_encoder_kwargs = kwargs

    def __getstate__(self):
        d = super().__getstate__()
        del d['bc_encoder']
        return d

    def __setstate__(self, d):
        super().__setstate__(d)
        self.bc_encoder = BertClient(*self._bc_encoder_args, **self._bc_encoder_kwargs)

    @BE._train_required
    def encode(self, texts: List[str], is_tokenized=False) -> bytes:
        vec = self.bc_encoder.encode(texts, is_tokenized=is_tokenized)
        return super().encode(vec)

    def train(self, texts: List[str], is_tokenized=False) -> None:
        vec = self.bc_encoder.encode(texts, is_tokenized=is_tokenized)
        return super().train(vec)
