from typing import List, Tuple, Any, Dict

from ..base import *
from ..encoder import CompositionalEncoder


class BaseIndexer(TrainableBase):
    def add(self, keys: Any, docs: Any, *args, **kwargs): pass

    def query(self, keys: Any, top_k: int, *args, **kwargs) -> List[List[Tuple[Any, float]]]: pass

    def close(self):
        super().close()


class BaseBinaryIndexer(BaseIndexer):
    def __init__(self):
        super().__init__()

    def add(self, keys: bytes, docs: bytes, *args, **kwargs):
        pass

    def query(self, keys: bytes, top_k: int, *args, **kwargs) -> List[List[Tuple[int, float]]]:
        pass


class BaseTextIndexer(BaseIndexer):
    def add(self, keys: List[int], docs: Any, *args, **kwargs): pass

    def query(self, keys: List[int], top_k: int, *args, **kwargs) -> List[Any]: pass


class MultiheadIndexer(CompositionalEncoder):
    def add(self, keys: Any, docs: Any, head_name: str, *args, **kwargs) -> None:
        if not self.is_pipeline and head_name in self.component:
            self.component[head_name].add(keys, docs)

    def query(self, keys: bytes, top_k: int, *args, **kwargs) -> List[List[Tuple[Dict, float]]]:
        result_score = self.component['binary_indexer'].query(keys, top_k)
        all_ids = list(set(d[0] for id_score in result_score for d in id_score if d[0] >= 0))
        result_doc = self.component['text_indexer'].query(all_ids)
        id2doc = {d_id: d_content for d_id, d_content in zip(all_ids, result_doc)}
        return [[(id2doc[d_id], d_score) for d_id, d_score in id_score] for id_score in result_score]
