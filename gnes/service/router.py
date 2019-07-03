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
from typing import Dict, List

from .base import BaseService as BS, MessageHandler, ServiceError
from ..helper import batch_iterator
from ..postprocessor.base import BaseChunkPostprocessor, BaseDocPostprocessor, BasePostprocessor
from ..proto import gnes_pb2


class RouterService(BS):
    handler = MessageHandler(BS.handler)

    @handler.register(NotImplementedError)
    def _handler_default(self, msg: 'gnes_pb2.Message'):
        pass


class PublishRouterService(BS):
    handler = MessageHandler(BS.handler)

    @handler.register(NotImplementedError)
    def _handler_default(self, msg: 'gnes_pb2.Message'):
        msg.envelope.num_part = self.args.num_part


class MapRouterService(RouterService):
    handler = MessageHandler(BS.handler)

    # MapRouterService dont support distributed training for now

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

    # as MapRouterService dont support distributed training for now,
    # there is no need for ReduceRouterService to collected reduced training message

    def _post_init(self):
        self.pending_resp_index = defaultdict(list)  # type: Dict[str, List]
        self.pending_resp_query = defaultdict(list)  # type: Dict[str, List]
        self.chunk_postprocessor = BaseChunkPostprocessor()
        self.doc_postprocessor = BaseDocPostprocessor()
        self.base_postprocessor = BasePostprocessor()

    @handler.register(gnes_pb2.Response.IndexResponse)
    def _handler_index(self, msg: 'gnes_pb2.Message'):
        req_id = msg.envelope.request_id
        self.pending_resp_index[req_id].append(msg)
        len_resp = len(self.pending_resp_index[req_id])

        if len_resp == msg.envelope.num_part:
            self.base_postprocessor.apply(msg, self.pending_resp_index.pop(req_id))
        else:
            msg.response.index.status = gnes_pb2.Response.PENDING
            yield  # stop propagate "pending" signal

    @handler.register(gnes_pb2.Response.QueryResponse)
    def _handler_query(self, msg: 'gnes_pb2.Message'):
        req_id = msg.envelope.request_id
        self.pending_resp_query[req_id].append(msg)
        msg_parts = self.pending_resp_index[req_id]
        num_shards = len(msg_parts)

        if self.args.num_part == num_shards:
            if msg.response.search.level == gnes_pb2.Response.QueryResponse.CHUNK:
                self.chunk_postprocessor.apply(msg, self.pending_resp_index.pop(req_id))
            elif msg.response.search.level == gnes_pb2.Response.QueryResponse.DOCUMENT:
                self.doc_postprocessor.apply(msg, self.pending_resp_index.pop(req_id))
            else:
                raise ServiceError('i dont know how to handle QueryResponse at level %s' % msg.response.search.level)
        else:
            msg.response.search.status = gnes_pb2.Response.PENDING
            yield  # stop propagate "pending" signal
