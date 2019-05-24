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
from .base import build_socket, SocketType, ComponentNotLoad
from ..helper import set_logger
import zmq.decorators as zmqd
from typing import List
import zmq
import ctypes
import numpy as np
import uuid
import threading
import json
import time


class HttpService:
    def __init__(self, args=None):
        self.args = args
        self.logger = set_logger(self.__class__.__name__, self.args.verbose)
        self.identity = str(uuid.uuid4())
        self.result = {}
        self.index_suc_msg = 'index succesful'
        self.train_suc_msg = 'train succesful'

    def run(self):
        self._run()

    def _run(self):
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=self.args.max_workers)

        async def post_handler(request):
            try:
                data = await asyncio.wait_for(request.json(), 10)
                mode = data["mode"] if "mode" in data else "query"
                self.logger.info('receiver request: %s' % mode)
                if mode == 'query':
                    result = await loop.run_in_executor(executor,
                                                        self.query,
                                                        data['texts'])
                    res_f = []
                    if result:
                        for _1 in range(len(result.querys)):
                            res_ = []
                            for _ in range(len(result.querys[_1].results)):
                                res_.append(result.querys[_1].results[_].chunk.text)
                            res_f.append(res_)

                elif mode == 'index':
                    result = await loop.run_in_executor(executor,
                                                        self.index,
                                                        data['texts'])
                    res_f = self.index_suc_msg
                elif mode == 'train':
                    result = await loop.run_in_executor(executor,
                                                        self.train,
                                                        data['texts'])
                    res_f = self.train_suc_msg
                else:
                    res_f = 'specific the right mode: train, index, query'

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
                                  client_max_size=10**10,
                                  handler_args=handler_args)
            app.router.add_route('post', '/gnes', post_handler)
            srv = yield from loop.create_server(app.make_handler(),
                                                'localhost',
                                                self.args.http_port)
            self.logger.info('Server started at localhost:%d ...' % self.args.http_port)
            return srv

        loop.run_until_complete(init(loop))
        loop.run_forever()

    def query(self, texts: List[str]):
        search_req = gnes_pb2.SearchRequest()
        search_req._request_id = str(uuid.uuid4()).encode('ascii')
        search_req.time_out = self.args.timeout
        search_req.top_k = 10

        doc = gnes_pb2.Document()
        doc.id = np.random.randint(0, ctypes.c_uint(-1).value)
        doc.text = ' '.join(texts)
        doc.text_chunks.extend(texts)
        doc.doc_size = len(texts)
        doc.is_parsed = True

        search_req.doc.CopyFrom(doc)

        # query = gnes_pb2.Query()
        # query.top_k = top_k

        search_message = gnes_pb2.Message()
        search_message.client_id = self.identity
        search_message.msg_id = search_req._request_id
        search_message.num_part = 1
        search_message.part_id = 1
        search_message.mode = gnes_pb2.Message.QUERY
        search_message.docs.extend([doc])

        for i, chunk in enumerate(doc.text_chunks):
            q = search_message.querys.add()
            q.id = i
            q.text = chunk
            q.top_k = search_req.top_k

        search_message.route = self.__class__.__name__
        search_message.is_parsed = True

        return self._send_recv_msg(search_message)

    def index(self, texts: List[List[str]]):
        message = self._gen_msg(texts)
        message.mode = gnes_pb2.Message.INDEX
        return self._send_recv_msg(message)

    def train(self, texts: List[List[str]]):
        message = self._gen_msg(texts)
        message.mode = gnes_pb2.Message.TRAIN
        return self._send_recv_msg(message)

    def _gen_msg(self, texts: List[List[str]]):
        message = gnes_pb2.Message()
        message.client_id = self.identity
        message.msg_id = str(uuid.uuid4())

        for text in texts:
            doc = message.docs.add()
            doc.id = np.random.randint(0, ctypes.c_uint(-1).value)
            doc.text = ' '.join(text)
            doc.text_chunks.extend(text)
            doc.doc_size = len(text)
            doc.is_parsed = True

        message.route = self.__class__.__name__
        message.is_parsed = True
        return message

    def _send_recv_msg(self, message):
        with zmq.Context() as ctx:
            ctx.setsockopt(zmq.LINGER, 0)
            self.logger.info('connecting sockets...')
            in_sock, _ = build_socket(ctx, self.args.host_in,
                                      self.args.port_in,
                                      self.args.socket_in,
                                      None)
            out_sock, _ = build_socket(ctx, self.args.host_out,
                                       self.args.port_out,
                                       self.args.socket_out,
                                       None)
            send_message(out_sock, message, timeout=self.args.timeout)
            N, res = 0, None
            while N < 10:
                res = recv_message(in_sock)
                if res:
                    break
                else:
                    time.sleep(0.2)
                    N += 1
            self.logger.info('message received, closing socket')
            in_sock.close()
            out_sock.close()

        return res
