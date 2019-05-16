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

from gnes.proto import gnes_pb2
import asyncio
from aiohttp import web
from concurrent.futures import ThreadPoolExecutor
from ..messaging import send_message, recv_message
import zmq
import ctypes
import numpy as np
import uuid
import threading


class Message_handler:
    def __init__(self, args=None):
        self.args = args
        self.timeout = args.timeout if args else 5000
        self.port_in = args.port_in if args else 8599
        self.port_out = args.port_out if args else 8598
        self.host_out = args.host_out if args else "localhost"
        self.host_in = args.host_in if args else "localhost"

        self.context = zmq.Context()
        self.sender = self.context.socket(zmq.PUSH)
        self.sender.connect('tcp://%s:%d' % (self.host_out, self.port_out))

        self.identity = str(uuid.uuid4()).encode('ascii')
        self.receiver = self.context.socket(zmq.SUB)
        self.receiver.setsockopt(zmq.SUBSCRIBE, self.identity)
        self.receiver.connect('tcp://%s:%d' % (self.host_in, self.port_in))

        self._auto_recv = threading.Thread(target=self._recv_msg)

        self.result = {}

    def _recv_msg(self):
        while True:
            msg = recv_message(self.receiver)
            if msg.msg_id in self.result:
                self.result[msg.msg_id].append(msg)
            else:
                self.result[msg.msg_id] = [msg]

    def mes_gen(self, texts, index=False):
        message = gnes_pb2.Message()
        message.client_id = self.identity
        message.msg_id = str(uuid.uuid4()).encode('ascii')
        if index:
            message.mode = gnes_pb2.Message.INDEX
        else:
            message.mode = gnes_pb2.Message.QUERY

        for text in texts:
            doc = message.docs.add()
            doc.id = np.random.randint(0, ctypes.c_uint(-1).value)
            doc.text = ' '.join(text)
            doc.text_chunks.extend(text)
            doc.doc_size = len(text)
            doc.is_parsed = True

        return message

    def index(self, texts):
        message = self.mes_gen(texts, True)
        send_message(self.sender, message, timeout=self.timeout)

    def query(self, texts):
        message = self.mes_gen(texts)
        send_message(self.sender, message, timeout=self.timeout)
        while True:
            if message.msg_id in self.result:
                res = self.result[message.msg_id]
                del self.result[message.msg_id]
                break
        return res
