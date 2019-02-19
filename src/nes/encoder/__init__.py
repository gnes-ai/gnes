from typing import List


class BaseEncoder:
    def __init__(self, **kwargs): pass

    def encode(self, **kwargs): pass


class BaseBinaryEncoder(BaseEncoder):
    def encode(self, texts: List[str]) -> bytes: pass
