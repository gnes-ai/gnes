from typing import List

from ..document import BaseDocument
from ..helper import set_logger


class BaseIndexer:
    def __init__(self, verbose=False, **kwargs):
        self.logger = set_logger(self.__class__.__name__, verbose)

    def add(self, **kwargs): pass

    def query(self, **kwargs): pass

    def dump(self, **kwargs): pass

    def load(self, **kwargs): pass


class BaseBinaryIndexer(BaseIndexer):
    def __init__(self):
        super().__init__()

    def add(self, vectors: bytes, doc_ids: bytes):
        pass

    def query(self, keys: bytes, top_k: int) -> List[int]:
        pass


class BaseTextIndexer(BaseIndexer):
    def add(self, docs: List[BaseDocument]):
        pass

    def query(self, keys: List[int]) -> List[BaseDocument]:
        pass
