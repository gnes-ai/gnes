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

from .base import get_unary_score, CombinedScoreFn
from typing import List, Tuple
import numpy as np


class WeightedChunkScoreFn(CombinedScoreFn):
    """score = d_chunk.weight * relevance * q_chunk.weight"""

    def __call__(self, last_score: 'gnes_pb2.Response.QueryResponse.ScoredResult.Score',
                 q_chunk: 'gnes_pb2.Chunk',
                 d_chunk: 'gnes_pb2.Chunk', *args, **kwargs):
        q_chunk_weight = get_unary_score(value=q_chunk.weight,
                                         name='query chunk weight',
                                         offset=q_chunk.offset)
        d_chunk_weight = get_unary_score(value=d_chunk.weight,
                                         name='document chunk weight',
                                         doc_id=d_chunk.doc_id,
                                         offset=d_chunk.offset)

        return super().__call__(last_score, q_chunk_weight, d_chunk_weight)


class WeightedChunkOffsetScoreFn(CombinedScoreFn):
    """
    score = d_chunk.weight * relevance * offset_divergence * q_chunk.weight
    offset_divergence is calculated based on doc_type:
        TEXT && VIDEO && AUDIO: offset is 1-D
        IMAGE: offset is 2-D
    """

    def __call__(self, last_score: 'gnes_pb2.Response.QueryResponse.ScoredResult.Score',
                 q_chunk: 'gnes_pb2.Chunk',
                 d_chunk: 'gnes_pb2.Chunk', *args, **kwargs):
        q_chunk_weight = get_unary_score(value=q_chunk.weight,
                                         name='query chunk weight',
                                         offset=str(q_chunk.offset))
        d_chunk_weight = get_unary_score(value=d_chunk.weight,
                                         name='document chunk weight',
                                         doc_id=d_chunk.doc_id,
                                         offset=str(d_chunk.offset))
        offset_divergence = get_unary_score(value=self._cal_divergence(q_chunk, d_chunk),
                                            name='offset divergence')
        return super().__call__(last_score, q_chunk_weight, d_chunk_weight, offset_divergence)

    @staticmethod
    def _cal_divergence(q_chunk: 'gnes_pb2.Chunk', d_chunk: 'gnes_pb2.Chunk'):
        if q_chunk.offset_nd and d_chunk.offset_nd:
            return 1 / (1 + np.sqrt((q_chunk.offset_nd[0] - d_chunk.offset_nd[0]) ** 2 +
                                    (q_chunk.offset_nd[1] - d_chunk.offset_nd[1]) ** 2))
        else:
            return np.abs(q_chunk.offset - d_chunk.offset)


class CoordChunkScoreFn(CombinedScoreFn):
    """
    score = relevance * query_coordination
    query_coordination: #chunks return / #chunks in this doc(query doc)
    """

    def __call__(self, last_score: 'gnes_pb2.Response.QueryResponse.ScoredResult.Score',
                 q_chunk: 'gnes_pb2.Chunk',
                 d_chunk: 'gnes_pb2.Chunk',
                 queried_results: List[List[Tuple]],
                 *args, **kwargs):
        query_coordination = get_unary_score(value=self._cal_query_coord(d_chunk, queried_results),
                                             name='query coordination')
        return super().__call__(last_score, query_coordination)

    def _cal_query_coord(self, d_chunk: 'gnes_pb2.Chunk', queried_results: List[List[Tuple]]):
        doc_id = d_chunk.doc_id
        total_chunks = self._context.num_chunks_in_doc(doc_id)
        queried_doc_id, _, _, _ = zip(*(queried_results[0]))
        recall_chunks = queried_doc_id.count(doc_id)
        return recall_chunks / total_chunks


class TFIDFChunkScoreFn(CombinedScoreFn):
    """
    score = relevance * tf(q_chunk) * (idf(q_chunk)**2)
    tf(q_chunk) is calculated based on the relevance of query result.
    tf(q_chunk) = number of queried chunks where relevance >= threshold
    idf(q_chunk) = log(total_chunks / tf(q_chunk) + 1)
    """

    def __init__(self, threshold: float = 0.8, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.threshold = threshold

    def __call__(self, last_score: 'gnes_pb2.Response.QueryResponse.ScoredResult.Score',
                 q_chunk: 'gnes_pb2.Chunk',
                 d_chunk: 'gnes_pb2.Chunk',
                 queried_results: List[List[Tuple]],
                 *args, **kwargs):
        tf_idf = get_unary_score(value=self._cal_tf_idf(queried_results),
                                             name='query tf-idf')
        return super().__call__(last_score, tf_idf)

    def _cal_tf_idf(self, queried_results: List[List[Tuple]]):
        _, _, _, queried_relevance = zip(*(queried_results[0]))
        tf = len(list(filter(lambda x: x >= self.threshold, queried_relevance)))

        total_chunks = self._context.num_chunks
        idf = np.log10(total_chunks / (tf + 1))
        return tf * (idf ** 2)


class BM25ChunkScoreFn(CombinedScoreFn):
    """
    score = relevance * idf(q_chunk) * tf(q_chunk) * (k1 + 1) / (tf(q_chunk) +
                            k1 * (1 - b + b * (chunk_in_doc / avg_chunk_in_doc)))

    in bm25 algorithm:
             idf(q_chunk) = log(1 + (doc_count - f(q_chunk) +0.5) / (f(q_chunk) + 0.5)),
    where f(q_chunk) is number of docs that contains q_chunk. In our system, this denotes number of docs
    appearing in query results.

    In elastic search, b = 0.75, k1 = 1.2
    """

    def __init__(self, threshold: float = 0.8, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.threshold = threshold
        self.k1 = 1.2
        self.b = 0.75

    def __call__(self, last_score: 'gnes_pb2.Response.QueryResponse.ScoredResult.Score',
                 q_chunk: 'gnes_pb2.Chunk',
                 d_chunk: 'gnes_pb2.Chunk',
                 queried_results: List[List[Tuple]],
                 *args, **kwargs):
        bm25 = get_unary_score(value=self._cal_bm25(d_chunk, queried_results),
                                             name='query bm25')
        return super().__call__(last_score, bm25)

    def _cal_bm25(self, d_chunk: 'gnes_pb2.Chunk', queried_results: List[List[Tuple]]):
        doc_id = d_chunk.doc_id
        _, _, _, queried_relevance = zip(*(queried_results[0]))
        tf = len(list(filter(lambda x: x >= self.threshold, queried_relevance)))

        total_chunks = self._context.num_chunks
        idf = np.log10(1 + (total_chunks - tf + 0.5) / (tf + 0.5))
        return idf * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b *
                                (self._context.num_chunks_in_doc(doc_id) * self._context.num_docs / self._context.num_chunks)))
