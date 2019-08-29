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
import json
from typing import List, Any, Union, Callable, Tuple

import numpy as np

from ..base import TrainableBase, CompositionalTrainableBase
from ..proto import gnes_pb2, blob2array


class BaseIndexer(TrainableBase):

    def add(self, keys: Any, docs: Any, weights: List[float], *args, **kwargs):
        pass

    def query(self, keys: Any, *args, **kwargs) -> List[Any]:
        pass

    def normalize_score(self, *args, **kwargs):
        pass

    def query_and_score(self, q_chunks: List[Union['gnes_pb2.Chunk', 'gnes_pb2.Document']], top_k: int) -> List[
        'gnes_pb2.Response.QueryResponse.ScoredResult']:
        raise NotImplementedError

    def score(self, *args, **kwargs) -> 'gnes_pb2.Response.QueryResponse.ScoredResult.Score':
        raise NotImplementedError


class BaseChunkIndexer(BaseIndexer):

    def add(self, keys: List[Tuple[int, int]], vectors: np.ndarray, weights: List[float], *args, **kwargs):
        pass

    def query(self, keys: np.ndarray, top_k: int, *args, **kwargs) -> List[List[Tuple]]:
        pass

    def query_and_score(self, q_chunks: List['gnes_pb2.Chunk'], top_k: int, *args, **kwargs) -> List[
        'gnes_pb2.Response.QueryResponse.ScoredResult']:
        vecs = [blob2array(c.embedding) for c in q_chunks]
        queried_results = self.query(np.concatenate(vecs, 0), top_k=top_k)
        results = []
        for q_chunk, topk_chunks in zip(q_chunks, queried_results):
            for _doc_id, _offset, _weight, _relevance in topk_chunks:
                r = gnes_pb2.Response.QueryResponse.ScoredResult()
                r.chunk.doc_id = _doc_id
                r.chunk.offset = _offset
                r.chunk.weight = _weight
                r.score.CopyFrom(self.score(q_chunk, r.chunk, _relevance))
                results.append(r)
        return results

    def score(self, q_chunk: 'gnes_pb2.Chunk', d_chunk: 'gnes_pb2.Chunk',
              relevance) -> 'gnes_pb2.Response.QueryResponse.ScoredResult.Score':
        return ChunkScorer.eq1(q_chunk, d_chunk, relevance)


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
                r.score.CopyFrom(self.score(d, r.score))
            results.append(r)
        return results

    def score(self, d: 'gnes_pb2.Document', s: 'gnes_pb2.Response.QueryResponse.ScoredResult.Score', *args,
              **kwargs) -> 'gnes_pb2.Response.QueryResponse.ScoredResult.Score':
        return DocScorer.eq1(d, s)


class BaseKeyIndexer(BaseIndexer):

    def add(self, keys: List[Tuple[int, int]], weights: List[float], *args, **kwargs) -> int:
        pass

    def query(self, keys: List[int], *args, **kwargs) -> List[Tuple[int, int, float]]:
        pass


class ChunkScorer:

    @staticmethod
    def eq1(q_chunk: 'gnes_pb2.Chunk', d_chunk: 'gnes_pb2.Chunk',
            relevance):
        """
        score = d_chunk.weight * relevance * q_chunk.weight
        """
        score = gnes_pb2.Response.QueryResponse.ScoredResult.Score()
        score.value = d_chunk.weight * relevance * q_chunk.weight
        score.explained = json.dumps({
            'name': 'chunk-eq1',
            'operand': [{'name': 'd_chunk_weight',
                         'value': d_chunk.weight,
                         'doc_id': d_chunk.doc_id,
                         'offset': d_chunk.offset},
                        {'name': 'q_chunk_weight',
                         'value': q_chunk.weight,
                         'offset': q_chunk.offset},
                        {'name': 'relevance',
                         'value': relevance}],
            'op': 'prod',
            'value': score.value
        })
        return score


class DocScorer:

    @staticmethod
    def eq1(d: 'gnes_pb2.Document',
            s: 'gnes_pb2.Response.QueryResponse.ScoredResult.Score') -> 'gnes_pb2.Response.QueryResponse.ScoredResult.Score':
        """
        score *= d.weight
        :param d:
        :param s:
        :return:
        """
        s.value *= d.weight
        s.explained = json.dumps({
            'name': 'doc-eq1',
            'operand': [json.loads(s.explained),
                        {'name': 'doc_weight',
                         'value': d.weight,
                         'doc_id': d.doc_id}],
            'op': 'prod',
            'value': s.value
        })
        return s


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
