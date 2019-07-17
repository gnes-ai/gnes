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

from ..helper import set_logger
from ..proto import gnes_pb2_grpc, RequestGenerator


class HttpClient:
    def __init__(self, args=None):
        self.args = args
        self.logger = set_logger(self.__class__.__name__, self.args.verbose)

    def start(self):
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=self.args.max_workers)

        async def general_handler(request, parser, *args, **kwargs):
            try:
                data = await asyncio.wait_for(request.json(), 10)
                self.logger.info('data received, beigin processing')
                resp = await loop.run_in_executor(
                    executor,
                    stub_call,
                    parser([d.encode() for d in data.get('docs')] if hasattr(data, 'docs')
                           else data.get('query').encode(), *args, **kwargs))
                self.logger.info('handling finished, will send to user')
                return web.Response(body=json.dumps({'result': resp, 'meta': None}, ensure_ascii=False),
                                    status=200,
                                    content_type='application/json')
            except Exception as ex:
                return web.Response(body=json.dumps({'message': str(ex), 'type': type(ex)}),
                                    status=400,
                                    content_type='application/json')

        async def init(loop):
            # persistant connection or non-persistant connection
            handler_args = {'tcp_keepalive': False, 'keepalive_timeout': 25}
            app = web.Application(loop=loop,
                                  client_max_size=10 ** 10,
                                  handler_args=handler_args)
            app.router.add_route('post', '/train',
                                 lambda x: general_handler(x, RequestGenerator.train, batch_size=self.args.batch_size))
            app.router.add_route('post', '/index',
                                 lambda x: general_handler(x, RequestGenerator.index, batch_size=self.args.batch_size))
            app.router.add_route('post', '/query',
                                 lambda x: general_handler(x, RequestGenerator.query, top_k=self.args.top_k))
            srv = await loop.create_server(app.make_handler(),
                                           self.args.http_host,
                                           self.args.http_port)
            self.logger.info('http server listens to %s:%d ...' % (self.args.http_host, self.args.http_port))
            return srv

        def stub_call(req):
            res_f = None
            for r in req:
                res_f = stub._Call(r)
            return json.loads(MessageToJson(res_f))

        with grpc.insecure_channel(
                '%s:%s' % (self.args.grpc_host, self.args.grpc_port),
                options=[('grpc.max_send_message_length', 50 * 1024 * 1024),
                         ('grpc.max_receive_message_length', 50 * 1024 * 1024),
                         ('grpc.keepalive_timeout_ms', 100 * 1000)]) as channel:
            stub = gnes_pb2_grpc.GnesRPCStub(channel)
            loop.run_until_complete(init(loop))
            loop.run_forever()
