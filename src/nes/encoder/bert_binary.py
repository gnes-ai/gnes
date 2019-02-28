from typing import List

from bert_serving.client import BertClient

from . import BaseEncoder as BE
from .lopq import LOPQEncoder


class BertBinaryEncoder(LOPQEncoder):
    def __init__(self, num_bytes=10,
                 cluster_per_byte: int = 255,
                 backend: str = 'numpy',
                 pca_output_dim: int = 256,
                 *args, **kwargs):
        super().__init__(num_bytes, cluster_per_byte, backend, pca_output_dim)
        self.bc_encoder = BertClient(*args, **kwargs)

    @BE._train_required
    def encode(self, texts: List[str], is_tokenized=False) -> bytes:
        vec = self.bc_encoder.encode(texts, is_tokenized=is_tokenized)
        return super().encode(vec)

    @BE._as_train_func
    def train(self, texts: List[str], is_tokenized=False) -> None:
        vec = self.bc_encoder.encode(texts, is_tokenized=is_tokenized)
        return super().train(vec)
