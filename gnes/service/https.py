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

from .client import ClientService
from gnes.proto import gnes_pb2
import asyncio
from aiohttp import web
from concurrent.futures import ThreadPoolExecutor


class ClientServer:
    def __init__(self, args):
        self.client = ClientService(args)

        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=10)

        async def post_handler(request):
            keys = []
            try:
                data = await asyncio.wait_for(request.json(), 10)
                keys = await loop.run_in_executor(executor,
                                                  self.client.query, data['texts'])
                ok = True

            except TimeoutError:
                keys = []
                ok = False
                seq = 'null'
                searchid = 'null'

            ret_body =json.dumps({"data":keys, "meta":{}, "seq": seq,
                                 "searchid": searchid, "ok":ok}, ensure_ascii=False)
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
            self.logger.info('Server started at localhost:8081...')
            return srv

        loop.run_until_complete(init(loop))
        loop.run_forever()


