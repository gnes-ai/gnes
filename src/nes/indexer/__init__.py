from typing import List, Tuple, Any

from ..base import TrainableBase as TB
from ..document import BaseDocument


class BaseIndexer(TB):
    @TB._timeit
    def add(self, *args, **kwargs): pass

    @TB._timeit
    def query(self, *args, **kwargs) -> List[List[Tuple[Any, float]]]: pass


class BaseBinaryIndexer(BaseIndexer):
    def __init__(self):
        super().__init__()

    @TB._timeit
    def add(self, vectors: bytes, doc_ids: bytes):
        pass

    @TB._timeit
    def query(self, keys: bytes, top_k: int) -> List[List[Tuple[int, float]]]:
        pass


class BaseTextIndexer(BaseIndexer):
    @TB._timeit
    def add(self, docs: List[BaseDocument]): pass

    @TB._timeit
    def query(self, keys: List[int]) -> List[Any]: pass
