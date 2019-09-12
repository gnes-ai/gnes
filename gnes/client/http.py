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


import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

import grpc
from google.protobuf.json_format import MessageToJson

from ..helper import set_logger
from ..proto import gnes_pb2_grpc, RequestGenerator


class HttpClient:
    def __init__(self, args=None):
        self.args = args
        self.logger = set_logger(self.__class__.__name__, self.args.verbose)

    def start(self):
        try:
            from aiohttp import web
        except ImportError:
            self.logger.error('can not import aiohttp, it is not installed correctly. please do '
                              '"pip install gnes[aiohttp]"')
            return
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=self.args.max_workers)

        async def general_handler(request, parser, *args, **kwargs):
            try:
                data = dict()
                # # Option 1: uploading streaming chunk data
                # data = b""
                # async for chunk in request.content.iter_any():
                #     data += chunk
                # self.logger.info("received %d content" % len(data))

                # Option 2: uploading via Multipart-Encoded File
                post_data = await request.post()
                if 'query' in post_data.keys():
                    _file = post_data.get('query')
                    self.logger.info('query request from input file: %s' % _file.filename)
                    data['query'] = _file.file.read()
                elif 'docs' in post_data.keys():
                    files = post_data.getall('docs')
                    self.logger.info('index request from input files: %d files' % len(files))
                    data['docs'] = [_file.file.read() for _file in files]

                self.logger.info('data received')
                resp = await loop.run_in_executor(
                    executor,
                    stub_call,
                    parser([d for d in data.get('docs')] if hasattr(data, 'docs')
                           else data.get('query'), *args, **kwargs))
                self.logger.info('send back to user')
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
            self.logger.info('http server listens at %s:%d' % (self.args.http_host, self.args.http_port))
            return srv

        def stub_call(req):
            res_f = list(stub.StreamCall(req))[-1]
            return json.loads(MessageToJson(res_f))

        with grpc.insecure_channel(
                '%s:%s' % (self.args.grpc_host, self.args.grpc_port),
                options=[('grpc.max_send_message_length', self.args.max_message_size),
                         ('grpc.max_receive_message_length', self.args.max_message_size),
                         ('grpc.keepalive_timeout_ms', 100 * 1000)]) as channel:
            stub = gnes_pb2_grpc.GnesRPCStub(channel)
            loop.run_until_complete(init(loop))
            loop.run_forever()
