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

from ..helper import TimeContext
from ..proto import gnes_pb2_grpc, RequestGenerator


class BenchmarkClient:
    def __init__(self, args):

        all_bytes = [b'a' * args.request_length] * args.num_requests

        with grpc.insecure_channel(
                '%s:%d' % (args.grpc_host, args.grpc_port),
                options=[('grpc.max_send_message_length', args.max_message_size),
                         ('grpc.max_receive_message_length', args.max_message_size)]) as channel:
            stub = gnes_pb2_grpc.GnesRPCStub(channel)

            id = 0
            with TimeContext('StreamCall') as tc:
                resp = stub.StreamCall(RequestGenerator.index(all_bytes, args.batch_size))
                for r in resp:
                    assert r.request_id == id
                    id += 1
            stream_call_el = tc.duration

            with TimeContext('Call') as tc:
                for req in RequestGenerator.index(all_bytes, batch_size=1):
                    r = stub.Call(req)
                    assert r.request_id == req.request_id

            call_el = tc.duration

        print('num_requests     %d\n'
              'request_length   %d' % (args.num_requests, args.request_length))
        print('StreamCall       %3.3f s\n'
              'Call             %3.3f s\n' % (stream_call_el, call_el))
