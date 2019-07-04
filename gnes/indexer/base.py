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

from typing import List, Any, Union, Callable, Tuple

import numpy as np

from ..base import TrainableBase
from ..encoder.base import CompositionalEncoder


class BaseIndexer(TrainableBase):
    internal_index_path = 'int.indexer.bin'  # this is used when pickle dump is not enough for storing all info

    def add(self, keys: Any, docs: Any, weights: List[float], *args, **kwargs):
        pass

    def query(self, keys: Any, *args, **kwargs) -> List[Any]:
        pass


class BaseVectorIndexer(BaseIndexer):

    def add(self, keys: List[Tuple[int, int]], vectors: np.ndarray, weights: List[float], *args, **kwargs):
        pass

    def query(self, keys: np.ndarray, top_k: int, *args, **kwargs) -> List[List[Tuple]]:
        pass


class BaseTextIndexer(BaseIndexer):

    def add(self, keys: List[int], docs: Any, weights: List[float], *args, **kwargs):
        pass

    def query(self, keys: List[int], *args, **kwargs) -> List[Any]:
        pass


class BaseKeyIndexer(BaseIndexer):

    def add(self, keys: List[Tuple[int, int]], weights: List[float], *args, **kwargs) -> int:
        pass

    def query(self, keys: List[int], *args, **kwargs) -> List[Tuple[int, int, float]]:
        pass


class JointIndexer(CompositionalEncoder):

    @property
    def component(self):
        return self._component

    @component.setter
    def component(self, comps: Callable[[], Union[list, dict]]):
        if not callable(comps):
            raise TypeError('component must be a callable function that returns '
                            'a List[BaseIndexer]')
        if not getattr(self, 'init_from_yaml', False):
            self._component = comps()
        else:
            self.logger.info('component is omitted from construction, '
                             'as it is initialized from yaml config')

        self._binary_indexer = None
        self._doc_indexer = None
        for c in self.component:
            if isinstance(c, BaseVectorIndexer):
                self._binary_indexer = c
            elif isinstance(c, BaseTextIndexer):
                self._doc_indexer = c
        if not self._binary_indexer or not self._doc_indexer:
            raise ValueError('"JointIndexer" requires a valid pair of "BaseBinaryIndexer" and "BaseTextIndexer"')

    def add(self, keys: Any, docs: Any, *args,
            **kwargs) -> None:
        if isinstance(docs, np.ndarray):
            self._binary_indexer.add(keys, docs, *args, **kwargs)
        elif isinstance(docs, list):
            self._doc_indexer.add(keys, docs, *args, **kwargs)
        else:
            raise TypeError('can not find an indexer for doc type: %s' % type(docs))

    def query(self,
              keys: Any,
              top_k: int,
              *args,
              **kwargs) -> List[List[Tuple]]:
        topk_results = self._binary_indexer.query(keys, top_k, *args, **kwargs)
        doc_caches = dict()
        topk_results_with_docs = []
        for topk in topk_results:
            topk_wd = []
            for doc_id, offset, weight, score in topk:
                doc = doc_caches.get(doc_id, self._doc_indexer.query([doc_id])[0])
                doc_caches[doc_id] = doc
                topk_wd.append((doc_id, offset, weight, score, doc.chunks[offset]))
            topk_results_with_docs.append(topk_wd)
        return topk_results_with_docs
