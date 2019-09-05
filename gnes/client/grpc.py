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

import grpc
import time

import queue
from concurrent import futures

from gnes.proto import gnes_pb2_grpc

_TIMEOUT = 60 * 60 * 24


class BaseGrpcClient:

    def __init__(self, args):
        self.args = args

        self._channel = grpc.insecure_channel(
            '%s:%d' % (self.args.grpc_host, self.args.grpc_port),
            options={
                "grpc.max_send_message_length": -1,
                "grpc.max_receive_message_length": -1,
            }.items(),
        )
        # waits for the channel to be ready before we start sending messages
        grpc.channel_ready_future(self._channel).result()

        self._stub = gnes_pb2_grpc.GnesRPCStub(self._channel)

        self._response_callbacks = []

    def add_response_callback(self, callback):
        """callback will be invoked as callback(client, query_time)"""
        self._response_callbacks.append(callback)

    def send_request(self, request):
        """Non-blocking wrapper for a client's request operation."""
        raise NotImplementedError

    def start(self):
        pass

    def stop(self):
        pass

    def _handle_response(self, client, response, response_time):
        for callback in self._response_callbacks:
            callback(client, response, response_time)


class UnarySyncClient(BaseGrpcClient):

    def __init__(self, args):
        super().__init__(args)
        self._pool = futures.ThreadPoolExecutor(
            max_workers=self.args.max_concurrency)

    def send_request(self, request):
        # Send requests in seperate threads to support multiple outstanding rpcs
        # (See src/proto/grpc/testing/control.proto)
        self._pool.submit(self._dispatch_request, request)

    def stop(self):
        self._pool.shutdown(wait=True)
        self._stub = None

    def _dispatch_request(self, request):
        start_time = time.time()
        resp = self._stub.Call(request)
        end_time = time.time()
        self._handle_response(self, resp, end_time - start_time)


class UnaryAsyncClient(BaseGrpcClient):

    def send_request(self, request):
        # Use the Future callback api to support multiple outstanding rpcs
        start_time = time.time()
        response_future = self._stub.Call.future(self._request, _TIMEOUT)
        response_future.add_done_callback(
            lambda resp: self._response_received(start_time, resp))

    def _response_received(self, start_time, resp):
        resp = resp.result()
        end_time = time.time()
        self._handle_response(self, resp, end_time - start_time)

    def stop(self):
        self._stub = None


class _SyncStream(object):

    def __init__(self, stub, handle_response):
        self._stub = stub
        self._handle_response = handle_response
        self._is_streaming = False
        self._request_queue = queue.Queue()
        self._send_time_queue = queue.Queue()

    def send_request(self, request):
        self._send_time_queue.put(time.time())
        self._request_queue.put(request)

    def start(self):
        self._is_streaming = True
        response_stream = self._stub.StreamCall(self._request_generator())
        for resp in response_stream:
            self._handle_response(
                self, resp,
                time.time() - self._send_time_queue.get_nowait())

    def stop(self):
        self._is_streaming = False

    def _request_generator(self):
        while self._is_streaming:
            try:
                request = self._request_queue.get(block=True, timeout=1.0)
                yield request
            except queue.Empty:
                pass


class StreamingSyncClient(UnarySyncClient):

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

    def stop(self):
        for stream in self._streams:
            stream.stop()
        self._pool.shutdown(wait=True)
        self._stub = None
