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

from typing import List, Tuple, Any, Dict

import numpy as np

from ..base import TrainableBase
from ..encoder.base import CompositionalEncoder


class BaseIndexer(TrainableBase):
    internal_index_path = 'int.indexer.bin'  # this is used when pickle dump is not enough for storing all info

    def add(self, keys: Any, docs: Any, *args, **kwargs):
        pass

    def query(self, keys: Any, top_k: int, *args,
              **kwargs) -> List[List[Tuple[Any, float]]]:
        pass


class BaseBinaryIndexer(BaseIndexer):

    def add(self, keys: Any, docs: np.ndarray, *args, **kwargs):
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
            self.component[head_name].add(keys, docs, *args, **kwargs)

    def query(self,
              keys: Any,
              top_k: int,
              sent_recall_factor: int = 1,
              *args,
              **kwargs) -> List[List[Tuple[Dict, float]]]:
        topk_results = self.component['binary_indexer'].query(
            keys, top_k * sent_recall_factor, normalized_score=True)

        doc_caches = dict()
        topk_results_with_docs = []
        for topk in topk_results:
            topk_wd = []
            for (doc_id, offset), score in topk:
                doc = doc_caches.get(doc_id, self.component['doc_indexer'].query([doc_id])[0])
                doc_caches[doc_id] = doc
                chunk = doc.text_chunks[offset] if doc.text_chunks else doc.blob_chunks[offset]
                topk_wd.append(((doc_id, offset), score, (doc.doc_size, chunk)))
            topk_results_with_docs.append(topk_wd)
        return topk_results_with_docs
