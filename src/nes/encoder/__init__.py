from typing import List

from bert_serving.client import BertClient


class BaseEncoder:
    def __init__(self, *args, **kwargs): pass

    def encode(self, *args, **kwargs): pass


class BaseBinaryEncoder(BaseEncoder):
    def encode(self, texts: List[str]) -> bytes: pass


class BertEncoder(BaseEncoder, BertClient):
    def __init__(self, *args, **kwargs):
        BertClient.__init__(*args, **kwargs)
