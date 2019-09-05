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
from typing import List, Any, Union, Callable, Tuple

import numpy as np

from ..base import TrainableBase, CompositionalTrainableBase
from ..proto import gnes_pb2, blob2array
from ..score_fn.base import get_unary_score, ModifierScoreFn


class BaseIndexer(TrainableBase):
    def __init__(self,
                 normalize_fn: 'BaseScoreFn' = ModifierScoreFn(),
                 score_fn: 'BaseScoreFn' = ModifierScoreFn(),
                 is_big_score_similar: bool = False,
                 *args, **kwargs):
        """
        Base indexer, a valid indexer must implement `add` and `query` methods
        :type score_fn: advanced score function
        :type normalize_fn: normalizing score function
        :type is_big_score_similar: when set to true, then larger score means more similar
        """
        super().__init__(*args, **kwargs)
        self.normalize_fn = normalize_fn
        self.score_fn = score_fn
        self.is_big_score_similar = is_big_score_similar

    def add(self, keys: Any, docs: Any, weights: List[float], *args, **kwargs):
        pass

    def query(self, keys: Any, *args, **kwargs) -> List[Any]:
        pass

    def query_and_score(self, q_chunks: List[Union['gnes_pb2.Chunk', 'gnes_pb2.Document']], top_k: int) -> List[
        'gnes_pb2.Response.QueryResponse.ScoredResult']:
        raise NotImplementedError


class BaseChunkIndexer(BaseIndexer):

    def add(self, keys: List[Tuple[int, int]], vectors: np.ndarray, weights: List[float], *args, **kwargs):
        pass

    def query(self, keys: np.ndarray, top_k: int, *args, **kwargs) -> List[List[Tuple]]:
        pass

    def query_and_score(self, q_chunks: List['gnes_pb2.Chunk'], top_k: int, *args, **kwargs) -> List[
        'gnes_pb2.Response.QueryResponse.ScoredResult']:
        vecs = [blob2array(c.embedding) for c in q_chunks]
        queried_results = self.query(np.stack(vecs), top_k=top_k)
        results = []
        for q_chunk, topk_chunks in zip(q_chunks, queried_results):
            for _doc_id, _offset, _weight, _relevance in topk_chunks:
                r = gnes_pb2.Response.QueryResponse.ScoredResult()
                r.chunk.doc_id = _doc_id
                r.chunk.offset = _offset
                r.chunk.weight = _weight
                _score = get_unary_score(value=_relevance,
                                         name=self.__class__.__name__,
                                         operands=[
                                             dict(name='doc_chunk',
                                                  doc_id=_doc_id,
                                                  offset=_offset),
                                             dict(name='query_chunk',
                                                  offset=q_chunk.offset)])
                _score = self.normalize_fn(_score)
                _score = self.score_fn(_score, q_chunk, r.chunk)
                r.score.CopyFrom(_score)
                results.append(r)
        return results


class BaseDocIndexer(BaseIndexer):

    def add(self, keys: List[int], docs: Any, weights: List[float], *args, **kwargs):
        pass

    def query(self, keys: List[int], *args, **kwargs) -> List['gnes_pb2.Document']:
        pass

    def query_and_score(self, docs: List['gnes_pb2.Response.QueryResponse.ScoredResult'], *args, **kwargs) -> List[
        'gnes_pb2.Response.QueryResponse.ScoredResult']:
        keys = [r.doc.doc_id for r in docs]
        results = []
        queried_results = self.query(keys, *args, **kwargs)
        for d, r in zip(queried_results, docs):
            if d:
                r.doc.CopyFrom(d)
                _score = self.normalize_fn(r.score)
                _score = self.score_fn(_score, d)
                r.score.CopyFrom(_score)
            results.append(r)
        return results


class BaseKeyIndexer(BaseIndexer):

    def add(self, keys: List[Tuple[int, int]], weights: List[float], *args, **kwargs) -> int:
        pass

    def query(self, keys: List[int], *args, **kwargs) -> List[Tuple[int, int, float]]:
        pass


class JointIndexer(CompositionalTrainableBase):

    @property
    def components(self):
        return self._component

    @components.setter
    def components(self, comps: Callable[[], Union[list, dict]]):
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
        for c in self.components:
            if isinstance(c, BaseChunkIndexer):
                self._binary_indexer = c
            elif isinstance(c, BaseDocIndexer):
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
