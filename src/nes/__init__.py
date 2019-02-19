from typing import Iterator

from .document import BaseDocument
from .encoder import *
from .helper import set_logger
from .indexer import *


class NES(BaseIndexer):
    def __init__(self, binary_encoder: BaseBinaryEncoder,
                 binary_indexer: BaseBinaryIndexer,
                 text_indexer: BaseTextIndexer,
                 batch_size: int = 128):
        super().__init__()
        self.binary_encoder = binary_encoder
        self.binary_indexer = binary_indexer
        self.text_indexer = text_indexer
        self.batch_size = batch_size

    def _add_batch(self, batch: List[BaseDocument]):
        bin_vectors = self.binary_encoder.encode([str(t) for t in batch])
        self.binary_indexer.add(bin_vectors)
        self.text_indexer.add(batch)

    def add(self, iter_doc: Iterator[BaseDocument]) -> None:
        cur_batch = []
        for doc in iter_doc:
            cur_batch.append(doc)
            if len(cur_batch) == self.batch_size:
                self._add_batch(cur_batch)
                cur_batch.clear()
        if cur_batch:
            self._add_batch(cur_batch)

    def query(self, queries: List[str], top_k: int) -> List[BaseDocument]:
        bin_queries = self.binary_encoder.encode(queries)
        doc_ids = self.binary_indexer.query(bin_queries, top_k)
        return self.text_indexer.query(doc_ids)
