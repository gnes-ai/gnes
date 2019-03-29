from typing import List, Tuple, Any, Iterator, Dict

from ..base import *
from ..document import BaseDocument
from ..encoder import CompositionalEncoder


class BaseIndexer(TrainableBase):
    def add(self, *args, **kwargs): pass

    def query(self, *args, **kwargs) -> List[List[Tuple[Any, float]]]: pass

    def close(self):
        super().close()


class BaseBinaryIndexer(BaseIndexer):
    def __init__(self):
        super().__init__()

    def add(self, vectors: bytes, doc_ids: bytes):
        pass

    def query(self, keys: bytes, top_k: int) -> List[List[Tuple[int, float]]]:
        pass


class BaseTextIndexer(BaseIndexer):
    def add(self, docs: Iterator[BaseDocument]): pass

    def query(self, keys: List[int]) -> List[Any]: pass


class MultiheadIndexer(CompositionalEncoder):
    def add(self, comp_name: str, *args) -> None:
        if not self.is_pipeline and comp_name in self.component:
            self.component[comp_name].add(*args)

    def query(self, bin_queries: bytes, top_k: int, *args, **kwargs) -> List[List[Tuple[Dict, float]]]:
        result_score = self.component['binary_indexer'].query(bin_queries, top_k)
        all_ids = list(set(d[0] for id_score in result_score for d in id_score if d[0] >= 0))
        result_doc = self.component['text_indexer'].query(all_ids)
        id2doc = {d_id: d_content for d_id, d_content in zip(all_ids, result_doc)}
        return [[(id2doc[d_id], d_score) for d_id, d_score in id_score] for id_score in result_score]
