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

from .. import __version__, __proto_version__
from ..client.base import ZmqClient
from ..helper import set_logger
from ..proto import gnes_pb2_grpc, gnes_pb2, router2str, add_route


class FrontendService:

    def __init__(self, args):
        self.logger = set_logger(self.__class__.__name__, args.verbose)
        self.server = grpc.server(
            ThreadPoolExecutor(max_workers=args.max_concurrency),
            options=[('grpc.max_send_message_length', args.max_message_size),
                     ('grpc.max_receive_message_length', args.max_message_size)])
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
            msg.envelope.gnes_version = __version__
            msg.envelope.proto_version = __proto_version__
            add_route(msg.envelope, FrontendService.__name__, self.args.identity)
            msg.request.CopyFrom(body)
            return msg

        def remove_envelope(self, m: 'gnes_pb2.Message'):
            resp = m.response
            resp.request_id = m.envelope.request_id
            m.envelope.routes[0].end_time.GetCurrentTime()
            if self.args.route_table:
                self.logger.info('route: %s' % router2str(m))
                route_time = []
                k = m.envelope.routes[0]
                total_duration = self.get_duration(k.start_time, k.end_time)

                sum_duration = 0
                for k in m.envelope.routes[1:]:
                    if k.first_start_time and k.last_end_time:
                        d = self.get_duration(k.first_start_time, k.last_end_time)
                    else:
                        d = self.get_duration(k.start_time, k.end_time)

                    route_time.append((k.service, d))
                    sum_duration += d

                def get_table_str(time_table):
                    return '\n'.join(
                        ['%40s\t%3.3fs\t%3d%%' % (k[0], k[1], k[1] / total_duration * 100) for k in
                         sorted(time_table, key=lambda x: x[1], reverse=True)])

                summary = [('system', total_duration - sum_duration),
                           ('total', total_duration),
                           ('job', sum_duration)]

                route_table = ('\n%s\n' % ('-' * 80)).join(
                    ['%40s\t%-6s\t%3s' % ('Breakdown', 'Time', 'Percent'), get_table_str(route_time),
                     get_table_str(summary)])
                self.logger.info('route table: \n%s' % route_table)

            return resp

        @staticmethod
        def get_duration(start_time, end_time):
            d_s = end_time.seconds - start_time.seconds
            d_n = end_time.nanos - start_time.nanos
            if d_s < 0 and d_n > 0:
                d_s = max(d_s + 1, 0)
                d_n = max(d_n - 1e9, 0)
            elif d_s > 0 and d_n < 0:
                d_s = max(d_s - 1, 0)
                d_n = max(d_n + 1e9, 0)
            return max(d_s + d_n / 1e9, 0)

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
                # network traffic control
                num_request = 0
                max_outstanding = 500

                for request in request_iterator:
                    timeout = 25
                    if self.args.timeout > 0:
                        timeout = min(0.5 * self.args.timeout, 50)

                    while num_request > 10:
                        try:
                            msg = zmq_client.recv_message(timeout)
                            yield self.remove_envelope(msg)
                            num_request -= 1
                        except TimeoutError:
                            if num_request > max_outstanding:
                                self.logger.warning("the network traffic exceed max outstanding (%d > %d)" % (num_request, max_outstanding))
                                continue
                            break
                    zmq_client.send_message(self.add_envelope(request, zmq_client), -1)
                    num_request += 1

                for _ in range(num_request):
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
