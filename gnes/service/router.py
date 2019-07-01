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
from typing import Dict

from .base import BaseService as BS, MessageHandler
from ..helper import batch_iterator
from ..proto import gnes_pb2


class RouterService(BS):
    handler = MessageHandler(BS.handler)

    @handler.register(NotImplementedError)
    def _handler_default(self, msg: 'gnes_pb2.Message'):
        pass


class MapRouterService(RouterService):
    handler = MessageHandler(BS.handler)

    @handler.register(gnes_pb2.Request.QueryRequest)
    def _handler_query_req(self, msg: 'gnes_pb2.Message'):
        pass

    @handler.register(gnes_pb2.Request.IndexRequest)
    def _handler_index_req(self, msg: 'gnes_pb2.Message'):
        if self.args.batch_size and self.args.batch_size > 0:
            batches = [b for b in batch_iterator(msg.request.index.docs, self.args.batch_size)]
            num_part = len(batches)
            for p_idx, b in enumerate(batches, start=1):
                _msg = gnes_pb2.Message()
                _msg.CopyFrom(msg)
                _msg.request.index.ClearField('docs')
                _msg.request.index.docs.extend(b)
                _msg.envelope.part_id = p_idx
                _msg.envelope.num_part = num_part
                yield _msg


class ReduceRouterService(RouterService):
    handler = MessageHandler(BS.handler)

    def _post_init(self):
        self.pending_result = defaultdict(list)  # type: Dict[str, list]

    @handler.register(gnes_pb2.Response.IndexResponse)
    def _handler_index(self, msg: 'gnes_pb2.Message'):
        req_id = msg.envelope.request_id
        self.pending_result[req_id].append(msg)
        len_result = len(self.pending_result[req_id])
        if len_result == msg.envelope.num_part:
            msg.response.index.status = gnes_pb2.Response.SUCCESS
            self.pending_result.pop(req_id)
        else:
            msg.response.index.status = gnes_pb2.Response.PENDING

    @handler.register(gnes_pb2.Response.QueryResponse)
    def _handler_query(self, msg: 'gnes_pb2.Message'):
        req_id = msg.envelope.request_id
        self.pending_result[req_id].append(msg)
        msg_parts = self.pending_result[req_id]
        num_shards = len(msg_parts)

        if self.args.num_part == num_shards:
            num_queries = len(msg_parts[0].response.search.result)
            chunks = [[] for _ in range(num_queries)]
            tk = len(msg.response.search.result[0].topk_results)
            for m in range(num_queries):
                chunks_all_shards = []
                for j in range(num_shards):
                    chunks_all_shards.extend(msg_parts[j].response.search.result[m].topk_results)

                chunks_all_shards = sorted(chunks[m], key=lambda x: -x.score)[:tk]
                msg.response.search.result[m].ClearField('topk_results')
                msg.response.search.result[m].topk_results.extend(chunks_all_shards)
            self.pending_result.pop(msg.envelope.request_id)
        else:
            msg.response.search.status = gnes_pb2.Response.PENDING
