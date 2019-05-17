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
from typing import List
import zmq
import ctypes
import numpy as np
import uuid
import threading
import json


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
        self._auto_recv.setDaemon(1)
        self._auto_recv.start()

        self.result = {}
        self.index_suc_msg = 'suc'

        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=100)

        async def post_handler(request):
            try:
                data = await asyncio.wait_for(request.json(), 10)
                mode = data["mode"] if "mode" in data else "query"
                print('receiver request', request, data)
                if mode == 'query':
                    result = await loop.run_in_executor(executor,
                                                        self.query,
                                                        data['texts'])
                    res_f = []
                    for _1 in range(len(result.querys)):
                        res_ = []
                        for _ in range(len(result.querys[_1].results)):
                            res_.append(result.querys[_1].results[_].chunk.text)
                        res_f.append(res_)

                else:
                    result = await loop.run_in_executor(executor,
                                                        self.index,
                                                        data['texts'])
                    res_f = self.index_suc_msg

                ok = 1
            except TimeoutError:
                res_f = ''
                ok = 0
            ret_body = json.dumps({"result": res_f, "meta": {}, "ok": str(ok)},ensure_ascii=False)
            return web.Response(body=ret_body)

        @asyncio.coroutine
        def init(loop):
            # persistant connection or non-persistant connection
            handler_args = {"tcp_keepalive": False, "keepalive_timeout": 25}
            app = web.Application(loop=loop,
                                  client_max_size=1024**4,
                                  handler_args=handler_args)
            app.router.add_route('post', '/query', post_handler)
            srv = yield from loop.create_server(app.make_handler(), 'localhost', 80)
            print('Server started at localhost:80...')
            return srv

        loop.run_until_complete(init(loop))
        loop.run_forever()

    def index(self, texts: List[List[str]]):

        message = gnes_pb2.Message()
        message.client_id = self.identity
        message.msg_id = str(uuid.uuid4()).encode('ascii')
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

        return self._send_recv_msg(message)

    def query(self, texts: List[str]):
        message = gnes_pb2.Message()
        message.client_id = self.identity
        message.msg_id = str(uuid.uuid4()).encode('ascii')

        doc = gnes_pb2.Document()
        doc.id = np.random.randint(0, ctypes.c_uint(-1).value)
        doc.text = ' '.join(texts)
        doc.text_chunks.extend(texts)
        doc.doc_size = len(texts)

        message.mode = gnes_pb2.Message.QUERY
        message.docs.extend([doc])

        for i, chunk in enumerate(doc.text_chunks):
            q = message.querys.add()
            q.id = i
            q.text = chunk

        return self._send_recv_msg(message)

    def _send_recv_msg(self, message):
        send_message(self.sender, message, timeout=self.timeout)
        while True:
            if message.msg_id in self.result:
                res = self.result[message.msg_id]
                del self.result[message.msg_id]
                break
            else:
                continue
        return res

    def _recv_msg(self):
        while True:
            msg = recv_message(self.receiver)
            self.result[msg.msg_id] = msg
