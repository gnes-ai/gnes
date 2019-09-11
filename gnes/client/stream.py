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

import queue
from concurrent import futures

from .base import GrpcClient


class _SyncStream:

    def __init__(self, stub, handle_response):
        self._stub = stub
        self._handle_response = handle_response
        self._is_streaming = False
        self._request_queue = queue.Queue()

    def send_request(self, request):
        self._request_queue.put(request)

    def start(self):
        self._is_streaming = True
        response_stream = self._stub.StreamCall(self._request_generator())
        for resp in response_stream:
            self._handle_response(self, resp)

    def stop(self):
        self._is_streaming = False

    def _request_generator(self):
        while self._is_streaming:
            try:
                request = self._request_queue.get(block=True, timeout=1.0)
                yield request
            except queue.Empty:
                pass


class UnarySyncClient(GrpcClient):

    def __init__(self, args):
        super().__init__(args)
        self._pool = futures.ThreadPoolExecutor(
            max_workers=self.args.max_concurrency)
        self._response_callbacks = []

    def send_request(self, request):
        # Send requests in seperate threads to support multiple outstanding rpcs
        self._pool.submit(self._dispatch_request, request)

    def close(self):
        self._pool.shutdown(wait=True)
        super().close()

    def _dispatch_request(self, request):
        resp = self._stub.Call(request)
        self._handle_response(self, resp)

    def _handle_response(self, client, response):
        for callback in self._response_callbacks:
            callback(client, response)

    def add_response_callback(self, callback):
        """callback will be invoked as callback(client, response)"""
        self._response_callbacks.append(callback)


class StreamingClient(UnarySyncClient):

    def __init__(self, args):
        super().__init__(args)

        self._streams = [
            _SyncStream(self._stub, self._handle_response)
            for _ in range(self.args.max_concurrency)
        ]
        self._curr_stream = 0

    def send_request(self, request):
        # Use a round_robin scheduler to determine what stream to send on
        self._streams[self._curr_stream].send_request(request)
        self._curr_stream = (self._curr_stream + 1) % len(self._streams)

    def start(self):
        for stream in self._streams:
            self._pool.submit(stream.start)

    def close(self):
        for stream in self._streams:
            stream.stop()
        super().close()
