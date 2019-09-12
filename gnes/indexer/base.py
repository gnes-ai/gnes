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
from functools import wraps
from typing import List, Any, Union, Callable, Tuple
from collections import defaultdict

import numpy as np

from ..base import TrainableBase, CompositionalTrainableBase
from ..proto import gnes_pb2, blob2array
from ..score_fn.base import get_unary_score, ModifierScoreFn


class BaseIndexer(TrainableBase):
    def __init__(self,
                 normalize_fn: 'BaseScoreFn' = None,
                 score_fn: 'BaseScoreFn' = None,
                 is_big_score_similar: bool = False,
                 *args, **kwargs):
        """
        Base indexer, a valid indexer must implement `add` and `query` methods
        :type score_fn: advanced score function
        :type normalize_fn: normalizing score function
        :type is_big_score_similar: when set to true, then larger score means more similar
        """
        super().__init__(*args, **kwargs)
        self.normalize_fn = normalize_fn if normalize_fn else ModifierScoreFn()
        self.score_fn = score_fn if score_fn else ModifierScoreFn()
        self.normalize_fn._context = self
        self.score_fn._context = self
        self.is_big_score_similar = is_big_score_similar
        self._num_docs = 0
        self._num_chunks = 0
        self._num_chunks_in_doc = defaultdict(int)

    def add(self, keys: Any, docs: Any, weights: List[float], *args, **kwargs):
        pass

    def query(self, keys: Any, *args, **kwargs) -> List[Any]:
        pass

    def query_and_score(self, q_chunks: List[Union['gnes_pb2.Chunk', 'gnes_pb2.Document']], top_k: int) -> List[
        'gnes_pb2.Response.QueryResponse.ScoredResult']:
        raise NotImplementedError

    @property
    def num_docs(self):
        return self._num_docs

    @property
    def num_chunks(self):
        return self._num_chunks


class BaseChunkIndexer(BaseIndexer):
    """Storing chunks and their vector representations """

    def __init__(self, helper_indexer: 'BaseChunkIndexerHelper' = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper_indexer = helper_indexer

    def add(self, keys: List[Tuple[int, int]], vectors: np.ndarray, weights: List[float], *args, **kwargs):
        """
        adding new chunks and their vector representations
        :param keys: list of (doc_id, offset) tuple
        :param vectors: vector representations
        :param weights: weight of the chunks
        """
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
                _score = self.score_fn(_score, q_chunk, r.chunk, queried_results)
                r.score.CopyFrom(_score)
                results.append(r)
        return results

    @staticmethod
    def update_counter(func):
        @wraps(func)
        def arg_wrapper(self, keys: List[Tuple[int, int]], *args, **kwargs):
            doc_ids, _ = zip(*keys)
            self._num_docs += len(set(doc_ids))
            self._num_chunks += len(keys)
            for doc_id in doc_ids:
                self._num_chunks_in_doc[doc_id] += 1
            return func(self, keys, *args, **kwargs)

        return arg_wrapper

    @staticmethod
    def update_helper_indexer(func):
        @wraps(func)
        def arg_wrapper(self, keys: List[Tuple[int, int]], vectors: np.ndarray, weights: List[float], *args, **kwargs):
            r = func(self, keys, vectors, weights, *args, **kwargs)
            if self.helper_indexer:
                self.helper_indexer.add(keys, weights, *args, **kwargs)
            return r

        return arg_wrapper

    @property
    def num_docs(self):
        if self.helper_indexer:
            return self.helper_indexer._num_docs
        else:
            return self._num_docs

    @property
    def num_chunks(self):
        if self.helper_indexer:
            return self.helper_indexer._num_chunks
        else:
            return self._num_chunks

    def num_chunks_in_doc(self, doc_id: int):
        if self.helper_indexer:
            return self.helper_indexer._num_chunks_in_doc[doc_id]
        else:
            self.logger.warning('enable helper_indexer to track num_chunks_in_doc')


class BaseDocIndexer(BaseIndexer):
    """Storing documents and contents """

    def add(self, keys: List[int], docs: List['gnes_pb2.Document'], *args, **kwargs):
        """
        adding new docs and their protobuf representation
        :param keys: list of doc_id
        :param docs: list of protobuf Document objects
        """
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

    @staticmethod
    def update_counter(func):
        @wraps(func)
        def arg_wrapper(self, keys: List[int], docs: List['gnes_pb2.Document'], *args, **kwargs):
            self._num_docs += len(keys)
            self._num_chunks += sum(len(d.chunks) for d in docs)
            return func(self, keys, docs, *args, **kwargs)

        return arg_wrapper


class BaseChunkIndexerHelper(BaseChunkIndexer):
    """A helper class for storing chunk info, doc mapping, weights.
    This is especially useful when ChunkIndexer can not store these information by itself
    """

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
