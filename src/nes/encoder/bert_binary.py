from typing import List

from bert_serving.client import BertClient

from .lopq import LOPQEncoder
from ..base import TrainableBase as TB
from ..helper import memcached


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

    @TB._train_required
    @TB._timeit
    @memcached
    def encode(self, texts: List[str], is_tokenized: bool = False) -> bytes:
        vec = self.bc_encoder.encode(texts, is_tokenized=is_tokenized)
        return super().encode(vec)

    @TB._as_train_func
    @TB._timeit
    def train(self, texts: List[str], is_tokenized: bool = False) -> None:
        vec = self.bc_encoder.encode(texts, is_tokenized=is_tokenized)
        return super().train(vec)
