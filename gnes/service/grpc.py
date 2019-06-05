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

import multiprocessing
import threading
from concurrent import futures

import grpc

from .base import BaseService as BS, MessageHandler
from ..helper import set_logger
from ..proto import gnes_pb2, gnes_pb2_grpc, send_message, recv_message

_THREAD_CONCURRENCY = multiprocessing.cpu_count()
LOGGER = set_logger(__name__)


class ClientService(BS):
    handler = MessageHandler(BS.handler)
    use_event_loop = False

    def _post_init(self):
        self.result = []


class GNESServicer(gnes_pb2_grpc.GnesRPCServicer):

    def __init__(self, args):
        self.args = args
        self.logger = set_logger(self.__class__.__name__, self.args.verbose)
        self.zmq_client = ClientService(args)

    def add_envelope(self, body: 'gnes_pb2.Request'):
        msg = gnes_pb2.Message()
        msg.envelope.client_id = self.zmq_client.identity
        msg.envelope.request_id = body.request_id
        msg.envelope.part_id = 1
        msg.envelope.num_part = 1
        msg.envelope.timeout = 5000
        r = msg.envelope.routes.add()
        r.service = self.zmq_client.__class__.__name__
        r.timestamp.GetCurrentTime()
        msg.request.CopyFrom(body)
        return msg

    def Train(self, request, context):
        msg = self.add_envelope(request)
        send_message(self.zmq_client.out_sock, msg, self.args.timeout)
        resp = recv_message(self.zmq_client.in_sock, self.args.timeout)
        return resp.body

    def Index(self, request, context):
        msg = self.add_envelope(request)
        send_message(self.zmq_client.out_sock, msg, self.args.timeout)
        resp = recv_message(self.zmq_client.in_sock, self.args.timeout)
        return resp.body

    def Search(self, request, context):
        msg = self.add_envelope(request)
        send_message(self.zmq_client.out_sock, msg, self.args.timeout)
        resp = recv_message(self.zmq_client.in_sock, self.args.timeout)
        return resp.body


def serve(args):
    # Initialize GRPC Server
    LOGGER.info('start a grpc server with %d workers ...' % _THREAD_CONCURRENCY)
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=_THREAD_CONCURRENCY))

    # Initialize Services
    gnes_pb2_grpc.add_GnesRPCServicer_to_server(GNESServicer(args), server)

    # Start GRPC Server
    bind_address = '{0}:{1}'.format(args.grpc_host, args.grpc_port)
    # server.add_insecure_port('[::]:' + '5555')
    server.add_insecure_port(bind_address)
    server.start()
    LOGGER.info('grpc service is listening at: %s' % bind_address)

    # Keep application alive
    forever = threading.Event()
    forever.wait()
