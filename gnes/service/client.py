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

import ctypes
import uuid
from typing import List, Optional

import numpy as np
import zmq

from gnes.proto import gnes_pb2
from .base import BaseService as BS, MessageHandler
from ..messaging import *


class ClientService(BS):
    handler = MessageHandler(BS.handler)

    def _post_init(self):
        self.result = []

    @handler.register(MessageType.DEFAULT.name)
    def _handler_default(self, msg: 'gnes_pb2.Message', out: 'zmq.Socket'):
        self.result.append(msg)
        self.logger.info('num of part finished %.2f%%' %
                         (len(self.result) / msg.num_part * 100))

    def index(self, texts: List[List[str]],
              is_train: bool = False) -> Optional['gnes_pb2.Message']:

        message = gnes_pb2.Message()
        message.client_id = self.identity
        message.msg_id = str(uuid.uuid4())
        message.num_part = 1
        message.part_id = 1
        if is_train:
            message.mode = gnes_pb2.Message.TRAIN
        else:
            message.mode = gnes_pb2.Message.INDEX

        for text in texts:
            doc = message.docs.add()
            doc.id = np.random.randint(0, ctypes.c_uint(-1).value)
            doc.text = ' '.join(text)
            doc.text_chunks.extend(text)
            doc.doc_size = len(text)
            doc.is_parsed = True

        message.route = self.__class__.__name__
        message.is_parsed = True

        send_message(self.out_sock, message, timeout=self.args.timeout)

        if self.args.wait_reply and not is_train:
            self.is_handler_done.wait(self.args.timeout)
            if self.result:
                res = self.result.pop()
                self.is_handler_done.clear()
                return res

    def query(self, texts: List[str],
              top_k: int = 10) -> Optional['gnes_pb2.Message']:
        doc = gnes_pb2.Document()
        doc.id = np.random.randint(0, ctypes.c_uint(-1).value)
        doc.text = ' '.join(texts)
        doc.text_chunks.extend(texts)
        doc.doc_size = len(texts)
        doc.is_parsed = True

        search_message = gnes_pb2.Message()
        search_message.client_id = self.identity
        search_message.msg_id = str(uuid.uuid4())
        search_message.num_part = 1
        search_message.part_id = 1
        search_message.mode = gnes_pb2.Message.QUERY
        search_message.docs.extend([doc])

        for i, chunk in enumerate(doc.text_chunks):
            q = search_message.querys.add()
            q.id = i
            q.text = chunk
            q.top_k = top_k

        search_message.route = self.__class__.__name__
        search_message.is_parsed = True

        send_message(self.out_sock, search_message, timeout=self.args.timeout)

        if self.args.wait_reply:
            self.is_handler_done.wait(self.args.timeout)
            if self.result:
                res = self.result.pop()
                self.is_handler_done.clear()
                return res
