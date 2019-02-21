from typing import List


class BaseEncoder:
    def __init__(self, *args, **kwargs): pass

    def encode(self, *args, **kwargs): pass


class BaseBinaryEncoder(BaseEncoder):
    def encode(self, texts: List[str]) -> bytes: pass
