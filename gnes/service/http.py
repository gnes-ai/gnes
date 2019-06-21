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
import json
from concurrent.futures import ThreadPoolExecutor

import grpc
from aiohttp import web
from google.protobuf.json_format import MessageToJson

from ..helper import set_logger, batch_iterator
from ..proto import gnes_pb2, gnes_pb2_grpc


class HttpService:
    def __init__(self, args=None):
        self.args = args
        self.logger = set_logger(self.__class__.__name__, self.args.verbose)

    def run(self):
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=self.args.max_workers)

        def index_request_gen(data):
            req = gnes_pb2.Request()
            for raw_text in data['docs']:
                if raw_text.strip():
                    d = req.index.docs.add()
                    d.raw_text = raw_text
            yield req

        def train_request_gen(data):
            batch_size = data.get('batch_size', self.args.batch_size)
            p = [r for r in data['docs'] if r.strip()]
            for pi in batch_iterator(p, batch_size):
                req = gnes_pb2.Request()
                for raw_text in pi:
                    d = req.train.docs.add()
                    d.raw_text = raw_text
                yield req
            req = gnes_pb2.Request()
            req.control.command = gnes_pb2.Request.ControlRequest.FLUSH
            yield req

        def query_request_gen(data):
            top_k = data.get('top_k', self.args.top_k)
            if top_k <= 0:
                raise ValueError('"top_k: %d" is not a valid number' % top_k)

            req = gnes_pb2.Request()
            req.search.query.raw_text = data['query']
            req.search.top_k = top_k
            yield req

        async def general_handler(request, parser):
            try:
                data = await asyncio.wait_for(request.json(), 10)
                resp = await loop.run_in_executor(executor,
                                                  self._grpc_call,
                                                  parser(data))
                return web.Response(body=json.dumps({'result': resp, 'meta': None}, ensure_ascii=False),
                                    status=200,
                                    content_type='application/json')
            except Exception as ex:
                return web.Response(body=json.dumps({'message': ex.message, 'type': type(ex)}), status=400,
                                    content_type='application/json')

        async def init(loop):
            # persistant connection or non-persistant connection
            handler_args = {'tcp_keepalive': False, 'keepalive_timeout': 25}
            app = web.Application(loop=loop,
                                  client_max_size=10 ** 10,
                                  handler_args=handler_args)
            app.router.add_route('post', '/gnes/train', lambda x: general_handler(x, train_request_gen))
            app.router.add_route('post', '/gnes/index', lambda x: general_handler(x, index_request_gen))
            app.router.add_route('post', '/gnes/query', lambda x: general_handler(x, query_request_gen))
            srv = await loop.create_server(app.make_handler(),
                                           self.args.http_host,
                                           self.args.http_port)
            self.logger.info('Server started at: %d ...' % self.args.http_port)
            return srv

        loop.run_until_complete(init(loop))
        loop.run_forever()

    def _grpc_call(self, req):
        with grpc.insecure_channel(
                '%s:%s' % (self.args.grpc_host, self.args.grpc_port),
                options=[('grpc.max_send_message_length', 50 * 1024 * 1024),
                         ('grpc.max_receive_message_length', 50 * 1024 * 1024)]) as channel:
            stub = gnes_pb2_grpc.GnesRPCStub(channel)
            res_f = None
            for _req in req:
                res_f = stub._Call(_req)
            return json.loads(MessageToJson(res_f))
