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

from .base import BaseReduceRouter, BaseTopkReduceRouter


class DocFillReducer(BaseReduceRouter):
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
    Gather all chunks by their doc_id, result in a topk doc list
    """

    def get_key(self, x: 'gnes_pb2.Response.QueryResponse.ScoredResult') -> str:
        return x.chunk.doc_id

    def set_key(self, x: 'gnes_pb2.Response.QueryResponse.ScoredResult', k: str):
        x.doc.doc_id = k


class ChunkTopkReducer(BaseTopkReduceRouter):
    """
    Gather all chunks by their chunk_id, aka doc_id-offset, result in a topk chunk list
    """

    def get_key(self, x: 'gnes_pb2.Response.QueryResponse.ScoredResult') -> str:
        return '%d-%d' % (x.chunk.doc_id, x.chunk.offset)

    def set_key(self, x: 'gnes_pb2.Response.QueryResponse.ScoredResult', k: str):
        x.chunk.doc_id, x.chunk.offset = map(int, k.split('-'))
