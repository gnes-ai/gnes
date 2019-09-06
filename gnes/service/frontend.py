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


import threading
from concurrent.futures import ThreadPoolExecutor

import grpc

from ..client.base import ZmqClient
from ..helper import set_logger
from ..proto import gnes_pb2_grpc, gnes_pb2, router2str


class FrontendService:

    def __init__(self, args):
        self.logger = set_logger(self.__class__.__name__, args.verbose)
        self.server = grpc.server(
            ThreadPoolExecutor(max_workers=args.max_concurrency),
            options=[('grpc.max_send_message_length', args.max_message_size * 1024 * 1024),
                     ('grpc.max_receive_message_length', args.max_message_size * 1024 * 1024)])
        self.logger.info('start a frontend with %d workers' % args.max_concurrency)
        gnes_pb2_grpc.add_GnesRPCServicer_to_server(self._Servicer(args), self.server)

        self.bind_address = '{0}:{1}'.format(args.grpc_host, args.grpc_port)
        self.server.add_insecure_port(self.bind_address)

    def __enter__(self):
        self.server.start()
        self.logger.critical('listening at: %s' % self.bind_address)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.server.stop(None)

    class _Servicer(gnes_pb2_grpc.GnesRPCServicer):

        def __init__(self, args):
            self.args = args
            self.logger = set_logger(FrontendService.__name__, args.verbose)
            self.zmq_context = self.ZmqContext(args)
            self.request_id_cnt = 0

        def add_envelope(self, body: 'gnes_pb2.Request', zmq_client: 'ZmqClient'):
            msg = gnes_pb2.Message()
            msg.envelope.client_id = zmq_client.identity if zmq_client.identity else ''
            if body.request_id is not None:
                msg.envelope.request_id = body.request_id
            else:
                msg.envelope.request_id = self.request_id_cnt
                self.request_id_cnt += 1
                self.logger.warning('request_id is missing, filled it with an internal counter!')
            msg.envelope.part_id = 1
            msg.envelope.num_part.append(1)
            msg.envelope.timeout = 5000
            r = msg.envelope.routes.add()
            r.service = FrontendService.__name__
            r.timestamp.GetCurrentTime()
            msg.request.CopyFrom(body)
            return msg

        def remove_envelope(self, m: 'gnes_pb2.Message'):
            resp = m.response
            resp.request_id = m.envelope.request_id
            self.logger.info('unpacking a message and return to client: %s' % router2str(m))
            return resp

        def Call(self, request, context):
            with self.zmq_context as zmq_client:
                zmq_client.send_message(self.add_envelope(request, zmq_client), self.args.timeout)
                return self.remove_envelope(zmq_client.recv_message(self.args.timeout))

        def Train(self, request, context):
            return self.Call(request, context)

        def Index(self, request, context):
            return self.Call(request, context)

        def Search(self, request, context):
            return self.Call(request, context)

        def StreamCall(self, request_iterator, context):
            with self.zmq_context as zmq_client:
                for request in request_iterator:
                    zmq_client.send_message(self.add_envelope(request, zmq_client), self.args.timeout)
                    msg = zmq_client.recv_message(self.args.timeout)
                    yield self.remove_envelope(msg)

        class ZmqContext:
            """The zmq context class."""

            def __init__(self, args):
                self.args = args
                self.tlocal = threading.local()
                self.tlocal.client = None

            def __enter__(self):
                """Enter the context."""
                client = ZmqClient(self.args)
                self.tlocal.client = client
                return client

            def __exit__(self, exc_type, exc_value, exc_traceback):
                """Exit the context."""
                self.tlocal.client.close()
                self.tlocal.client = None
