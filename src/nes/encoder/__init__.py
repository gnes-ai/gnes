from typing import List

from bert_serving.client import BertClient

from src.nes.encoder.lopq import LOPQ


class BaseEncoder:
    def __init__(self, *args, **kwargs): pass

    def encode(self, *args, **kwargs): pass


class BaseBinaryEncoder(BaseEncoder):
    def encode(self, texts: List[str]) -> bytes: pass


class BertEncoder(BaseEncoder, BertClient):
    def __init__(self, *args, **kwargs):
        BertClient.__init__(*args, **kwargs)


class PQEncoder(BaseEncoder, LOPQ):
    def __init__(self, k, m, num_clusters):
        super().__init__(k, m, num_clusters)
