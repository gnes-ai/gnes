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

import time
import threading
import queue
from concurrent import futures

from .base import GrpcClient, ResponseHandler


class SyncClient(GrpcClient):
    handler = ResponseHandler(GrpcClient.handler)

    def __init__(self, args):
        super().__init__(args)
        self._pool = futures.ThreadPoolExecutor(
            max_workers=self.args.max_concurrency)

    def send_request(self, request):
        # Send requests in seperate threads to support multiple outstanding rpcs
        self._pool.submit(self.call, request)

    def close(self):
        self._pool.shutdown(wait=True)
        super().close()


class StreamingClient(GrpcClient):
    handler = ResponseHandler(GrpcClient.handler)

    def __init__(self, args):
        super().__init__(args)

        self._request_queue = queue.Queue(maxsize=1000)
        self._is_streaming = threading.Event()

        self._dispatch_thread = threading.Thread(target=self._start)
        self._dispatch_thread.setDaemon(True)

    def send_request(self, request):
        self._request_queue.put(request, block=True)

        # create a new streaming call
        if not self._is_streaming.is_set():
            self._dispatch_thread.start()

    def _start(self):
        self._is_streaming.set()
        self.stream_call(self._request_generator())
        self._is_streaming.clear()

    def _request_generator(self):
        while self._is_streaming.is_set():
            try:
                request = self._request_queue.get(block=True, timeout=5.0)
                if request is None:
                    break
                yield request
            except queue.Empty:
                continue
            except Exception as e:
                print('exception: %s' % str(e))
                break

    @handler.register(NotImplementedError)
    def _handler_default(self, resp: 'gnes_pb2.Response'):
        raise NotImplementedError

    def close(self):
        self._is_streaming.clear()
        self._dispatch_thread.join()
        super().close()
