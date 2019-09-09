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

from typing import List
import numpy as np

from .base import BaseReduceRouter, BaseTopkReduceRouter, BaseEmbedReduceRouter
from ..proto import blob2array


class DocFillReducer(BaseReduceRouter):
    """
    Gather all documents raw content from multiple shards.
    This is only useful when you have
    - multiple doc-indexer and docs are spreaded over multiple shards.
    - require full-doc retrieval with the original content, not just an doc id
    Ideally, only each doc can only belong to one shard.
    """
    def apply(self, msg: 'gnes_pb2.Message', accum_msgs: List['gnes_pb2.Message'], *args, **kwargs):
        final_docs = []
        for idx in range(len(msg.response.search.topk_results)):
            # get result from all shards, some may return None, we only take the first non-None doc
            final_docs.append([m.response.search.topk_results[idx] for m in accum_msgs if
                               m.response.search.topk_results[idx].doc.WhichOneof('raw_data') is not None][0])
        msg.response.search.ClearField('topk_results')
        msg.response.search.topk_results.extend(final_docs)

        super().apply(msg, accum_msgs)


class DocTopkReducer(BaseTopkReduceRouter):
    """
    Gather all docs by their doc_id, result in a topk doc list
    """

    def get_key(self, x: 'gnes_pb2.Response.QueryResponse.ScoredResult') -> str:
        return x.doc.doc_id

    def set_key(self, x: 'gnes_pb2.Response.QueryResponse.ScoredResult', k: str):
        x.doc.doc_id = k


class Chunk2DocTopkReducer(BaseTopkReduceRouter):
    """
    Gather all chunks by their doc_id, result in a topk doc list.
    This is almost always useful, as the final result should be group by doc_id
    not chunk
    """

    def get_key(self, x: 'gnes_pb2.Response.QueryResponse.ScoredResult') -> str:
        return x.chunk.doc_id

    def set_key(self, x: 'gnes_pb2.Response.QueryResponse.ScoredResult', k: str):
        x.doc.doc_id = k


class ChunkTopkReducer(BaseTopkReduceRouter):
    """
    Gather all chunks by their chunk_id from all shards, aka doc_id-offset, result in a topk chunk list
    """

    def get_key(self, x: 'gnes_pb2.Response.QueryResponse.ScoredResult') -> str:
        return '%d-%d' % (x.chunk.doc_id, x.chunk.offset)

    def set_key(self, x: 'gnes_pb2.Response.QueryResponse.ScoredResult', k: str):
        x.chunk.doc_id, x.chunk.offset = map(int, k.split('-'))


class ConcatEmbedRouter(BaseEmbedReduceRouter):
    """
    Gather all embeddings from multiple encoders and concat them on a specific axis.
    In default, concat will happen on the last axis.
    chunk_idx, doc_idx denote index in for loop used in BaseEmbedReduceRouter
    """

    def reduce_embedding(self, accum_msgs: List['gnes_pb2.Message'], msg_type: str, chunk_idx: int, doc_idx: int):
        if msg_type == 'query':
            return np.concatenate([blob2array(m.request.search.query.chunks[chunk_idx].embedding)
                                   for m in accum_msgs], axis=1)
        elif msg_type == 'index':
            return np.concatenate([blob2array(m.request.index.docs[doc_idx].chunks[chunk_idx].embedding)
                                   for m in accum_msgs], axis=1)
        else:
            self.logger.error('dont know how to handle %s' % msg_type)


class AvgEmbedRouter(BaseEmbedReduceRouter):
    """
    Gather all embeddings from multiple encoders and do average on a specific axis.
    In default, average will happen on the first axis.
    chunk_idx, doc_idx denote index in for loop used in BaseEmbedReduceRouter
    """

    def reduce_embedding(self, accum_msgs: List['gnes_pb2.Message'], msg_type: str, chunk_idx: int, doc_idx: int):
        if msg_type == 'query':
            return np.mean([blob2array(m.request.search.query.chunks[chunk_idx].embedding)
                                   for m in accum_msgs], axis=0)
        elif msg_type == 'index':
            return np.mean([blob2array(m.request.index.docs[doc_idx].chunks[chunk_idx].embedding)
                                   for m in accum_msgs], axis=0)
        else:
            self.logger.error('dont know how to handle %s' % msg_type)