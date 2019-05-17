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

        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=10)

        async def post_handler(request):
            try:
                data = await asyncio.wait_for(request.json(), 10)
                print('receiver request', request, data)
                result = await loop.run_in_executor(executor,
                                                    self.query,
                                                    data['texts'])
                ok = 1
                res_f = []
                for _1 in range(len(result.querys)):
                    res_ = []
                    for _ in range(len(result.querys[_1].results)):
                        res_.append(result.querys[_1].results[_].chunk.text)
                    res_f.append(res_)

            except TimeoutError:
                res_f = ''
                ok = 0
            print(res_f)
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
            srv = yield from loop.create_server(app.make_handler(), 'localhost', 8081)
            print('Server started at localhost:8081...')
            return srv

        loop.run_until_complete(init(loop))
        loop.run_forever()

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

        doc = gnes_pb2.Document()
        doc.id = np.random.randint(0, ctypes.c_uint(-1).value)
        doc.text = ' '.join(texts)
        doc.text_chunks.extend(texts)
        doc.doc_size = len(texts)

        if index:
            message.mode = gnes_pb2.Message.INDEX
        else:
            message.mode = gnes_pb2.Message.QUERY

        message.docs.extend([doc])

        for i, chunk in enumerate(doc.text_chunks):
            q = message.querys.add()
            q.id = i
            q.text = chunk

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
            else:
                continue
        return res[0]
