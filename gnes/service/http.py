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


import asyncio
from aiohttp import web
from concurrent.futures import ThreadPoolExecutor

import grpc
from google.protobuf.json_format import MessageToJson
from ..helper import set_logger
from ..proto import gnes_pb2, gnes_pb2_grpc
from ..preprocessor.text import line2pb_doc_simple
from typing import List
import json
import random
import ctypes


class HttpService:
    def __init__(self, args=None):
        self.args = args
        self.logger = set_logger(self.__class__.__name__, self.args.verbose)
        self.msg_processor = {'query': self._query, 'index': self._index}

    def run(self):
        self._run()

    def _run(self):

        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=self.args.max_workers)

        async def post_handler(request):
            try:
                data = await asyncio.wait_for(request.json(), 10)
                texts = data['texts']
                tk = data['top_k'] if 'top_k' in data else 10
                mode = data['mode'] if 'mode' in data else 'query'
                self.logger.info('receiver request: %s' % mode)

                req = await loop.run_in_executor(executor,
                                                 self.msg_processor[mode],
                                                 texts, tk)
                ret = await loop.run_in_executor(executor,
                                                 self._grpc_call,
                                                 req)
                ok = 1
            except TimeoutError:
                ret = ''
                ok = 0
            ret_body = json.dumps({"result": ret, "meta": {}, "ok": str(ok)},ensure_ascii=False)
            return web.Response(body=ret_body)

        async def init(loop):
            # persistant connection or non-persistant connection
            handler_args = {"tcp_keepalive": False, "keepalive_timeout": 25}
            app = web.Application(loop=loop,
                                  client_max_size=10**10,
                                  handler_args=handler_args)
            app.router.add_route('post', '/gnes', post_handler)
            srv = await loop.create_server(app.make_handler(),
                                           self.args.http_host,
                                           self.args.http_port)
            self.logger.info('Server started at: %d ...' % self.args.http_port)
            return srv

        loop.run_until_complete(init(loop))
        loop.run_forever()

    def _query(self, texts: List[str], top_k: int, *args):
        doc = line2pb_doc_simple(texts)
        req = gnes_pb2.Request()
        req.search.query.CopyFrom(doc)
        req.search.top_k = top_k
        return req

    def _index(self, texts: List[List[str]], *args):
        p = [line2pb_doc_simple(l, random.randint(0, ctypes.c_uint(-1).value)) for l in texts]
        req = gnes_pb2.Request()
        req.index.docs.extend(p)
        return req

    def _grpc_call(self, req):
        self.logger.info('channel receive')
        with grpc.insecure_channel(
            '%s:%s' % (self.args.grpc_host, self.args.grpc_port),
            options=[('grpc.max_send_message_length', 50 * 1024 * 1024),
                     ('grpc.max_receive_message_length', 50 * 1024 * 1024)]) as channel:
            stub = gnes_pb2_grpc.GnesRPCStub(channel)
            res_f = stub._Call(req)
            self.logger.info('calling finished')
        self.logger.info('returning result')
        return json.loads(MessageToJson(res_f))
