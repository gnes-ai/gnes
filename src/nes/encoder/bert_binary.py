from typing import List

from bert_serving.client import BertClient

from . import BaseEncoder as BE
from .lopq import LOPQEncoder


class BertBinaryEncoder(BE):
    def __init__(self, ip: str = 'localhost',
                 port: int = 5555,
                 port_out: int = 5556,
                 dim_per_byte: int = 96,
                 backend='numpy'):
        super().__init__()
        bert_dim = 768
        self.bc_encoder = BertClient(ip, port, port_out)
        self.lopq_encoder = LOPQEncoder(bert_dim, dim_per_byte, backend=backend)

    @BE._train_required
    def encode(self, texts: List[str], is_tokenized=False):
        vec = self.bc_encoder.encode(texts, is_tokenized=is_tokenized)
        return self.lopq_encoder.encode(vec)

    @BE._as_train_func
    def train(self, texts: List[str], is_tokenized=False):
        vec = self.bc_encoder.encode(texts, is_tokenized=is_tokenized)
        self.lopq_encoder.train(vec)
