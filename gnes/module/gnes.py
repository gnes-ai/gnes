from typing import List, Tuple, Dict

from ..base import *
from ..document import *
from ..encoder import *
from ..helper import batching


class GNES(CompositionalEncoder):
    def train(self, lst_doc: List[BaseDocument], *args, **kwargs) -> None:
        sents = DocumentMapper(lst_doc).sent_id_sentence[1]
        self.component['encoder'].train(sents, *args, **kwargs)

    @train_required
    @batching
    def add(self, lst_doc: List[BaseDocument], *args, **kwargs) -> None:
        doc_mapper = DocumentMapper(lst_doc)
        ids, sents = doc_mapper.sent_id_sentence
        bin_vectors = self.component['encoder'].encode(sents, *args, **kwargs)
        self.component['binary_indexer'].add(ids, bin_vectors)
        self.component['text_indexer'].add(*doc_mapper.doc_id_document)

    @train_required
    def query(self, keys: List[str], top_k: int, *args, **kwargs) -> List[List[Tuple[Dict, float]]]:
        bin_queries = self.component['encoder'].encode(keys, *args, **kwargs)
        result_score = self.component['binary_indexer'].query(bin_queries, top_k)
        all_ids = list(set(d[0] for id_score in result_score for d in id_score if d[0] >= 0))
        result_doc = self.component['text_indexer'].query(all_ids)
        id2doc = {d_id: d_content for d_id, d_content in zip(all_ids, result_doc)}
        return [[(id2doc[d_id], d_score) for d_id, d_score in id_score] for id_score in result_score]
