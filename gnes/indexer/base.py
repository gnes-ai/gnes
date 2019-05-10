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

from ..base import TrainableBase
from ..encoder.base import CompositionalEncoder


class BaseIndexer(TrainableBase):
    internal_index_path = 'int.indexer.bin'    # this is used when pickle dump is not enough for storing all info

    def add(self, keys: Any, docs: Any, *args, **kwargs):
        pass

    def query(self, keys: Any, top_k: int, *args,
              **kwargs) -> List[List[Tuple[Any, float]]]:
        pass


class BaseBinaryIndexer(BaseIndexer):

    def __init__(self):
        super().__init__()

    def add(self, keys: bytes, docs: bytes, *args, **kwargs):
        pass

    def query(self, keys: bytes, top_k: int, *args,
              **kwargs) -> List[List[Tuple[int, float]]]:
        pass


class BaseTextIndexer(BaseIndexer):

    def add(self, keys: List[int], docs: Any, *args, **kwargs):
        pass

    def query(self, keys: List[int], top_k: int, *args, **kwargs) -> List[Any]:
        pass


class MultiheadIndexer(CompositionalEncoder):

    def add(self, keys: Any, docs: Any, head_name: str, *args,
            **kwargs) -> None:
        if not self.is_pipeline and head_name in self.component:
            self.component[head_name].add(keys, docs)

    def query(self,
              keys: Any,
              top_k: int,
              sent_recall_factor: int = 1,
              return_field: Optional[Tuple] = ('id', 'content'),
              *args,
              **kwargs) -> List[List[Tuple[Dict, float]]]:
        topk_results = self.component['binary_indexer'].query(
            keys, top_k * sent_recall_factor, normalized_score=True)

        doc_caches = dict()
        results = []
        for topk in topk_results:
            result = []
            for key, score in topk:
                doc_id, offset = key
                doc = doc_caches.get(doc_id, None)
                if doc is None:
                    doc = self.component['doc_indexer'].query([doc_id])[0]
                    doc_caches[doc_id] = doc

                chunk = doc.text_chunks[offset] if doc.text_chunks else doc.blob_chunks[offset]
                result.append(({
                    "doc_id": doc_id,
                    "doc_size": doc.doc_size,
                    "offset": offset,
                    "chunk": chunk
                }, score))
            results.append(result)
        return results