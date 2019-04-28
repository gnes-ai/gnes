#  Tencent is pleased to support the open source community by making GNES available.
#
#  Copyright (C) 2019 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# pylint: disable=low-comment-ratio


from collections import defaultdict
from typing import List, Tuple, Any, Dict, Optional

from ..base import *
from ..encoder.base import CompositionalEncoder


class BaseIndexer(TrainableBase):
    def add(self, keys: Any, docs: Any, *args, **kwargs): pass

    def query(self, keys: Any, top_k: int, *args, **kwargs) -> List[List[Tuple[Any, float]]]: pass


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

    def query(self, keys: bytes, top_k: int,
              sent_recall_factor: int = 10,
              return_field: Optional[Tuple] = ('id', 'content'), *args, **kwargs) -> List[
        List[Tuple[Dict, float]]]:
        sent_id_topk = self.component['binary_indexer'].query(keys, top_k * sent_recall_factor, normalized_score=True)

        # get unique sentence_id and query the corresponding doc_id
        sent_ids = list(set(s_id for id_score in sent_id_topk for s_id, score in id_score if s_id >= 0))
        doc_ids = self.component['sent_doc_indexer'].query(sent_ids)
        sent_id2doc_id = {s_id: d_id for s_id, d_id in zip(sent_ids, doc_ids)}

        # get unique doc_id and query the corresponding doc_content
        doc_ids = list(set(doc_ids))
        doc_contents = self.component['doc_content_indexer'].query(doc_ids)
        doc_id2content = {d_id: d_content for d_id, d_content in zip(doc_ids, doc_contents)}

        final_result = []
        for id_score in sent_id_topk:
            result = defaultdict(int)
            for s_id, score in id_score:
                normalizer = len(doc_id2content[sent_id2doc_id[s_id]]['sentences'])
                result[sent_id2doc_id[s_id]] += score / normalizer
            sorted_d = sorted(result.items(), key=lambda kv: kv[1], reverse=True)
            sorted_d = [({k: doc_id2content[d_id][k] for k in return_field} if return_field else doc_id2content[d_id],
                         score) for d_id, score in
                        sorted_d][:top_k]
            final_result.append(sorted_d)

        return final_result
