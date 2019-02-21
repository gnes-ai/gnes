from typing import List, Tuple, Any

from ..document import BaseDocument
from ..helper import set_logger


class BaseIndexer:
    def __init__(self, verbose: bool = False, *args, **kwargs):
        self.logger = set_logger(self.__class__.__name__, verbose)

    def add(self, *args, **kwargs): pass

    def query(self, *args, **kwargs) -> List[List[Tuple[Any, float]]]: pass

    def dump(self, *args, **kwargs): pass

    def load(self, *args, **kwargs): pass


class BaseBinaryIndexer(BaseIndexer):
    def __init__(self):
        super().__init__()

    def add(self, vectors: bytes, doc_ids: bytes):
        pass

    def query(self, keys: bytes, top_k: int) -> List[List[Tuple[int, float]]]:
        pass


class BaseTextIndexer(BaseIndexer):
    def add(self, docs: List[BaseDocument]):
        pass

    def query(self, keys: List[int]) -> List[BaseDocument]:
        pass
