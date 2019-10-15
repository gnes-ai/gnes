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


import os
import threading
from concurrent.futures import ThreadPoolExecutor

import grpc
from google.protobuf.json_format import MessageToJson

from ..client.base import ZmqClient
from ..helper import set_logger, make_route_table
from ..proto import gnes_pb2_grpc, gnes_pb2, router2str, add_route, add_version


class FrontendService:

    def __init__(self, args):
        if not args.proxy:
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')
        self.logger = set_logger(self.__class__.__name__, args.verbose)
        self.server = grpc.server(
            ThreadPoolExecutor(max_workers=args.max_concurrency),
            options=[('grpc.max_send_message_length', args.max_message_size),
                     ('grpc.max_receive_message_length', args.max_message_size)])
        self.logger.info('start a frontend with %d workers' % args.max_concurrency)
        gnes_pb2_grpc.add_GnesRPCServicer_to_server(self._Servicer(args), self.server)

        self.bind_address = '{0}:{1}'.format(args.grpc_host, args.grpc_port)
        self.server.add_insecure_port(self.bind_address)
        self._stop_event = threading.Event()

    def __enter__(self):
        self.server.start()
        self.logger.critical('listening at: %s' % self.bind_address)
        self._stop_event.clear()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.server.stop(None)
        self.stop()

    def stop(self):
        self._stop_event.set()

    def join(self):
        self._stop_event.wait()

    class _Servicer(gnes_pb2_grpc.GnesRPCServicer):

        def __init__(self, args):
            self.args = args
            self.logger = set_logger(FrontendService.__name__, args.verbose)
            self.zmq_context = self.ZmqContext(args)
            self.request_id_cnt = 0
            self.send_recv_kwargs = dict(
                check_version=self.args.check_version,
                timeout=self.args.timeout,
                squeeze_pb=self.args.squeeze_pb)
            self.pending_request = 0

        def add_envelope(self, body: 'gnes_pb2.Request', zmq_client: 'ZmqClient'):
            msg = gnes_pb2.Message()
            msg.envelope.client_id = zmq_client.args.identity
            if body.request_id is not None:
                msg.envelope.request_id = body.request_id
            else:
                msg.envelope.request_id = self.request_id_cnt
                self.request_id_cnt += 1
                self.logger.warning('request_id is missing, filled it with an internal counter!')
            msg.envelope.part_id = 1
            msg.envelope.num_part.append(1)
            msg.envelope.timeout = 5000
            add_version(msg.envelope)
            add_route(msg.envelope, FrontendService.__name__, self.args.identity)
            msg.request.CopyFrom(body)
            return msg

        def remove_envelope(self, m: 'gnes_pb2.Message'):
            resp = m.response
            resp.request_id = m.envelope.request_id
            m.envelope.routes[0].end_time.GetCurrentTime()
            if self.args.route_table:
                self.logger.info('route: %s' % router2str(m))
                self.logger.info('route table: \n%s' % make_route_table(m.envelope.routes, include_frontend=True))
            if self.args.dump_route:
                self.args.dump_route.write(MessageToJson(m.envelope, indent=0).replace('\n', '') + '\n')
                self.args.dump_route.flush()
            return resp

        def Call(self, request, context):
            with self.zmq_context as zmq_client:
                zmq_client.send_message(self.add_envelope(request, zmq_client), **self.send_recv_kwargs)
                return self.remove_envelope(zmq_client.recv_message(**self.send_recv_kwargs))

        def Train(self, request, context):
            return self.Call(request, context)

        def Index(self, request, context):
            return self.Call(request, context)

        def Search(self, request, context):
            return self.Call(request, context)

        def StreamCall(self, request_iterator, context):
            self.pending_request = 0

            def get_response(num_recv, blocked=False):
                if blocked:
                    self.logger.info('waiting for %d responses ...' % (num_recv))
                for _ in range(num_recv):
                    if blocked or zmq_client.receiver.poll(1):
                        msg = zmq_client.recv_message(**self.send_recv_kwargs)
                        self.pending_request -= 1
                        yield self.remove_envelope(msg)

            with self.zmq_context as zmq_client:

                for request in request_iterator:
                    self.logger.info('receive request: %s' % request.request_id)
                    num_recv = max(self.pending_request - self.args.max_pending_request, 1)
                    yield from get_response(num_recv, num_recv > 1)
                    self.logger.info('send new request into %d appending tasks' % (self.pending_request))
                    zmq_client.send_message(self.add_envelope(request, zmq_client), **self.send_recv_kwargs)
                    self.pending_request += 1

                self.logger.info('all requests are sent, waiting for the responses...')
                yield from get_response(self.pending_request, blocked=True)

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
