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
import ctypes
import json
import random
from concurrent.futures import ThreadPoolExecutor
from typing import List

import grpc
from aiohttp import web
from google.protobuf.json_format import MessageToJson

from ..helper import set_logger, batch_iterator
from ..preprocessor.text import line2pb_doc_simple
from ..proto import gnes_pb2, gnes_pb2_grpc


class HttpService:
    def __init__(self, args=None):
        self.args = args
        self.logger = set_logger(self.__class__.__name__, self.args.verbose)
        self.msg_processor = {'query': self._query,
                              'index': self._index,
                              'train': self._train}
        self.timeout_str = 'TimeoutError'

    def run(self):
        self._run()

    def _run(self):

        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=self.args.max_workers)

        async def post_handler(request):
            meta = None
            try:
                data = await asyncio.wait_for(request.json(), 10)
                texts = data['texts']
                top_k = data.get('top_k', self.args.default_k)
                if top_k <= 0:
                    raise ValueError('"top_k: %d" is not a valid number' % top_k)

                mode = data.get('mode', 'query')
                if mode not in self.msg_processor:
                    raise ValueError('request mode: %s is not supported' % mode)

                req = await loop.run_in_executor(executor,
                                                 self.msg_processor[mode],
                                                 texts, top_k)
                ret = await loop.run_in_executor(executor,
                                                 self._grpc_call,
                                                 req)
                return web.Response(body=json.dumps({'result': ret, 'meta': meta}, ensure_ascii=False),
                                    status=200,
                                    content_type='application/json')
            except Exception as ex:
                return web.Response(body=json.dumps({'message': ex.message, 'type': type(ex)}), status=400,
                                    content_type='application/json')

        async def init(loop):
            # persistant connection or non-persistant connection
            handler_args = {"tcp_keepalive": False, "keepalive_timeout": 25}
            app = web.Application(loop=loop,
                                  client_max_size=10 ** 10,
                                  handler_args=handler_args)
            app.router.add_route('post', '/gnes', post_handler)
            srv = await loop.create_server(app.make_handler(),
                                           self.args.http_host,
                                           self.args.http_port)
            self.logger.info('Server started at: %d ...' % self.args.http_port)
            return srv

        loop.run_until_complete(init(loop))
        loop.run_forever()

    def _train(self, texts: List[str], *args) -> List:
        p = [line2pb_doc_simple([l], random.randint(0, ctypes.c_uint(-1).value)) for l in texts]
        req_list = []
        for pi in batch_iterator(p, self.args.train_batch_size):
            req = gnes_pb2.Request()
            req.train.docs.extend(pi)
            req_list.append(req)
        return req_list

    def _query(self, texts: List[str], top_k: int, *args) -> gnes_pb2.Message:
        doc = line2pb_doc_simple(texts)
        req = gnes_pb2.Request()
        req.search.query.CopyFrom(doc)
        req.search.top_k = top_k
        return req

    def _index(self, texts: List[List[str]], *args) -> gnes_pb2.Message:
        p = [line2pb_doc_simple(l, random.randint(0, ctypes.c_uint(-1).value)) for l in texts]
        req = gnes_pb2.Request()
        req.index.docs.extend(p)
        return req

    def _grpc_call(self, req):
        with grpc.insecure_channel(
                '%s:%s' % (self.args.grpc_host, self.args.grpc_port),
                options=[('grpc.max_send_message_length', 50 * 1024 * 1024),
                         ('grpc.max_receive_message_length', 50 * 1024 * 1024)]) as channel:
            stub = gnes_pb2_grpc.GnesRPCStub(channel)
            if isinstance(req, list):
                for _req in req:
                    stub._Call(_req)
                req = gnes_pb2.Request()
                req.control.command = gnes_pb2.Request.ControlRequest.FLUSH
                res_f = stub._Call(req)
            else:
                res_f = stub._Call(req)
        return json.loads(MessageToJson(res_f))
