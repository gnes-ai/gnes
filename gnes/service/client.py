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


import uuid
from typing import List, Optional

import zmq
from zmq.utils import jsonapi

from .base import BaseService as BS, MessageHandler
from ..messaging import *
from gnes.proto import gnes_pb2


class ClientService(BS):
    handler = MessageHandler(BS.handler)

    def _post_init(self):
        self.result = []

    @handler.register(MessageType.DEFAULT.name)
    def _handler_default(self, msg: 'gnes_pb2.Message', out: 'zmq.Socket'):
        self.result.append(msg)

    def query(self, texts: List[str]) -> Optional['Message']:
        req_id = str(uuid.uuid4())

        idx_req = gnes_pb2.SearchRequest()
        idx_req._request_id = self.args.identity + req_id
        idx_req.time_out = self.args.timeout

        doc = gnes_pb2.Document()
        for i, text in enumerate(texts):
            chunk = gnes_pb2.Chunk()
            chunk.doc_id = req_id
            chunk.offset = i
            chunk.text = text
            # chunk.is_encodes = False
            doc.chunks.append(chunk)
        doc.is_parsed = True

        idx_req.query = gnes_pb2.Query()

        search_message = gnes_pb2.Message()
        search_message.msg_id = idx_req._request_id
        search_message.mode = gnes_pb2.Message.Mode.QUERY
        search_message.docs = [doc]
        search_message.query = query
        search_message.route = self.__class__.__name__
        search_message.is_parsed = True

        send_message(self.out_sock, search_message, timeout=self.args.timeout)

        # send_message(self.out_sock, Message(client_id=self.args.identity,
        #                                     req_id=req_id,
        #                                     msg_content=texts,
        #                                     route=self.__class__.__name__), timeout=self.args.timeout)
        if self.args.wait_reply:
            self.is_handler_done.wait(self.args.timeout)
            res = self.result.pop()
            # if self.args.merge_res:
            #     tmp = {}
            #     for part_id, content in jsonapi.loads(res.msg_content):
            #         content = jsonapi.loads(content)
            #         if part_id in tmp:
            #             tmp[part_id].append(content)
            #         else:
            #             tmp[part_id] = [content]
            #     merged = None
            #     for k in sorted(tmp.keys()):
            #         _t = list(zip(*tmp[k]))
            #         _top_k = len(_t[0][0])
            #         _t = [sorted([i for j in v for i in j],
            #                      key=lambda x: -x[1])[:_top_k]
            #               for v in _t]
            #         merged = merged + _t if merged else _t
            #     res.msg_content = merged
            return res
