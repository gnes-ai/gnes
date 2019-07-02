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
from ..proto import gnes_pb2, merge_routes


class RouterService(BS):
    handler = MessageHandler(BS.handler)

    @handler.register(NotImplementedError)
    def _handler_default(self, msg: 'gnes_pb2.Message'):
        pass


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

    @handler.register(gnes_pb2.Response.IndexResponse)
    def _handler_index(self, msg: 'gnes_pb2.Message'):
        req_id = msg.envelope.request_id
        self.pending_resp_index[req_id].append(msg)
        len_resp = len(self.pending_resp_index[req_id])

        if len_resp == msg.envelope.num_part:
            merge_routes(msg, self.pending_resp_index.pop(req_id))
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
                prev_msgs = self.pending_resp_index.pop(req_id)
                all_chunks = [r for m in prev_msgs for r in m.response.search.topk_results]
                doc_score = defaultdict(float)
                doc_score_explained = defaultdict(str)

                # count score by iterating over chunks
                for c in all_chunks:
                    doc_score[c.chunk.doc_id] += c.score
                    doc_score_explained += '%s\n' % c.score_explained

                # now convert chunk results to doc results
                msg.response.search.level = gnes_pb2.Response.QueryResponse.DOCUMENT_NOT_FILLED
                msg.response.search.ClearField('topk_results')

                # sort and add docs
                for k, v in sorted(doc_score.items(), key=lambda kv: -kv[1]):
                    r = msg.response.search.topk_results.add()
                    r.doc = gnes_pb2.Document()
                    r.doc.doc_id = k
                    r.score = v
                    r.score_explained = doc_score_explained[k]

                merge_routes(msg, prev_msgs)
            elif msg.response.search.level == gnes_pb2.Response.QueryResponse.DOCUMENT:
                prev_msgs = self.pending_resp_index.pop(req_id)
                final_docs = []
                for r, idx in enumerate(msg.response.search.topk_results):
                    # get result from all shards, some may return None, we only take the first non-None doc
                    final_docs.append([r for m in prev_msgs if
                                       m.response.search.topk_results[idx].doc.WhichOneOf('raw_data') is not None][0])

                # resort all doc result as the doc_weight has been applied
                final_docs = sorted(final_docs, key=lambda x: x.score, reverse=True)
                msg.response.search.ClearField('topk_results')
                msg.response.search.topk_results.extend(final_docs[:msg.response.search.top_k])

                merge_routes(msg, prev_msgs)
            else:
                raise ServiceError('i dont know how to handle QueryResponse at level %s' % msg.response.search.level)
        else:
            msg.response.search.status = gnes_pb2.Response.PENDING
            yield  # stop propagate "pending" signal
