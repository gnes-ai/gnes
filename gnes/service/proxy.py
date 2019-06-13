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

import zmq

from .base import BaseService as BS, MessageHandler
from ..helper import batch_iterator
from ..proto import gnes_pb2, send_message


class ProxyService(BS):
    handler = MessageHandler(BS.handler)

    @handler.register(NotImplementedError)
    def _handler_default(self, msg: 'gnes_pb2.Message', out: 'zmq.Socket'):
        send_message(out, msg, self.args.timeout)


class MapProxyService(ProxyService):
    handler = MessageHandler(BS.handler)

    # @handler.register(NotImplementedError)
    # def _handler_default(self, msg: 'gnes_pb2.Message', out: 'zmq.Socket'):
    #     raise NotImplementedError('%r can handle %r only' % (self.__class__, gnes_pb2.Request.IndexRequest))

    @handler.register(gnes_pb2.Request.QueryRequest)
    def _handler_query_req(self, msg: 'gnes_pb2.Message', out: 'zmq.Socket'):
        send_message(out, msg, self.args.timeout)

    @handler.register(gnes_pb2.Request.IndexRequest)
    def _handler_index_req(self, msg: 'gnes_pb2.Message', out: 'zmq.Socket'):
        if not self.args.batch_size or self.args.batch_size <= 0:
            send_message(out, msg, self.args.timeout)
        else:
            batches = [b for b in batch_iterator(msg.request.index.docs, self.args.batch_size)]
            num_part = len(batches)
            for p_idx, b in enumerate(batches, start=1):
                msg.request.index.ClearField('docs')
                msg.request.index.docs.extend(b)
                msg.envelope.part_id = p_idx
                msg.envelope.num_part = num_part
                send_message(out, msg, self.args.timeout)


class ReduceProxyService(ProxyService):
    handler = MessageHandler(BS.handler)

    def _post_init(self):
        self.pending_result = defaultdict(list)  # type: Dict[str, list]

    @handler.register(NotImplementedError)
    def _handler_default(self, msg: 'gnes_pb2.Message', out: 'zmq.Socket'):
        raise NotImplementedError('%r can handle %r only' % (self.__class__, gnes_pb2.Request.IndexRequest))

    @handler.register(gnes_pb2.Response.IndexResponse)
    def _handler_index(self, msg: 'gnes_pb2.Message', out: 'zmq.Socket'):
        self.pending_result[msg.envelope.request_id].append(msg)
        len_result = len(self.pending_result[msg.msg_id])
        if len_result == msg.envelope.num_part:
            msg.response.index.status = gnes_pb2.Response.SUCCESS
            send_message(out, msg, self.args.timeout)
            self.pending_result.pop(msg.envelope.request_id)

    @handler.register(gnes_pb2.Response.QueryResponse)
    def _handler_query(self, msg: 'gnes_pb2.Message', out: 'zmq.Socket'):
        self.pending_result[msg.envelope.request_id].append(msg)
        msg_parts = self.pending_result[msg.envelope.request_id]
        len_result = len(msg_parts)
        reduced_msg = msg_parts[0]
        tk = len(reduced_msg.response.search.result[0].topk_chunks)

        if self.args.num_part == len_result:
            num_queries = len(msg_parts[0].response.search.result)
            chunks = [[] for _ in range(num_queries)]
            self.logger.info(msg_parts)
            for m in range(num_queries):
                for j in range(len_result):
                    chunks[m].extend(msg_parts[j].response.search.result[m].topk_chunks)
            for m in range(num_queries):
                _chunks = sorted(chunks[m], key=lambda x: -x.score)[:tk]
                del reduced_msg.response.search.result[m].topk_chunks[:]
                reduced_msg.response.search.result[m].topk_chunks.extend(_chunks)

            send_message(out, reduced_msg, self.args.timeout)
            self.pending_result.pop(msg.envelope.request_id)
