from typing import List

from bert_serving.client import BertClient

from . import BaseEncoder as BE
from .lopq import LOPQEncoder


class BertBinaryEncoder(BE):
    def __init__(self, num_bytes=10,
                 dim_per_byte: int = 2,
                 cluster_per_byte: int = 255,
                 backend: str = 'numpy', *args, **kwargs):
        super().__init__()

        self.lopq_encoder = LOPQEncoder(num_bytes, dim_per_byte, cluster_per_byte, backend=backend)
        self.num_bytes = self.lopq_encoder.num_bytes
        self.bc_encoder = BertClient(*args, **kwargs)

    @BE._train_required
    def encode(self, texts: List[str], is_tokenized=False) -> bytes:
        vec = self.bc_encoder.encode(texts, is_tokenized=is_tokenized)
        return self.lopq_encoder.encode(vec)

    @BE._as_train_func
    def train(self, texts: List[str], is_tokenized=False) -> None:
        vec = self.bc_encoder.encode(texts, is_tokenized=is_tokenized)
        self.lopq_encoder.train(vec)
