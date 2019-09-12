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
import zmq
from termcolor import colored
from typing import Tuple, List, Union, Type

from ..helper import set_logger
from ..proto import gnes_pb2_grpc
from ..proto import send_message, gnes_pb2, recv_message
from ..service.base import build_socket


class ResponseHandler:

    def __init__(self, h: 'ResponseHandler' = None):
        self.routes = {k: v for k, v in h.routes.items()} if h else {}
        self.logger = set_logger(self.__class__.__name__)
        self._context = None

    def register(self, resp_type: Union[List, Tuple, type]):

        def decorator(f):
            if isinstance(resp_type, list) or isinstance(resp_type, tuple):
                for t in resp_type:
                    self.routes[t] = f
            else:
                self.routes[resp_type] = f
            return f

        return decorator

    def call_routes(self, resp: 'gnes_pb2.Response'):

        def get_default_fn(r_type):
            self.logger.warning(
                'cant find handler for response type: %s, fall back to the default handler'
                % r_type)
            f = self.routes.get(r_type, self.routes[NotImplementedError])
            return f

        self.logger.info(
            'received a response for request %d' % resp.request_id)
        if resp.WhichOneof('body'):
            body = getattr(resp, resp.WhichOneof('body'))
            resp_type = type(body)

            if resp_type in self.routes:
                fn = self.routes.get(resp_type)
            else:
                fn = get_default_fn(type(resp))

        self.logger.info('handling response with %s' % fn.__name__)
        return fn(self._context, resp)


class ZmqClient:

    def __init__(self, args):
        self.args = args
        self.logger = set_logger(self.__class__.__name__, self.args.verbose)
        self.ctx = zmq.Context()
        self.ctx.setsockopt(zmq.LINGER, 0)
        self.receiver, recv_addr = build_socket(
            self.ctx, self.args.host_in, self.args.port_in,
            self.args.socket_in, getattr(self, 'identity', None))
        self.sender, send_addr = build_socket(self.ctx, self.args.host_out,
                                              self.args.port_out,
                                              self.args.socket_out,
                                              getattr(self, 'identity', None))
        self.logger.info(
            'input %s:%s\t output %s:%s' %
            (self.args.host_in, colored(self.args.port_in, 'yellow'),
             self.args.host_out, colored(self.args.port_out, 'yellow')))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.sender.close()
        self.receiver.close()
        self.ctx.term()

    def send_message(self, message: "gnes_pb2.Message", timeout: int = -1):
        self.logger.debug('send message: %s' % message.envelope)
        send_message(self.sender, message, timeout=timeout)

    def recv_message(self, timeout: int = -1) -> gnes_pb2.Message:
        r = recv_message(
            self.receiver,
            timeout=timeout,
            check_version=self.args.check_version)
        self.logger.debug('recv a message: %s' % r.envelope)
        return r


class GrpcClient:
    """
    A Base Unary gRPC client which the other client application can build from.

    """

    handler = ResponseHandler()

    def __init__(self, args):
        self.args = args
        self.logger = set_logger(self.__class__.__name__, self.args.verbose)
        self.logger.info('setting up grpc insecure channel...')
        # A gRPC channel provides a connection to a remote gRPC server.
        self._channel = grpc.insecure_channel(
            '%s:%d' % (self.args.grpc_host, self.args.grpc_port),
            options={
                'grpc.max_send_message_length': -1,
                'grpc.max_receive_message_length': -1,
            }.items(),
        )
        self.logger.info('waiting channel to be ready...')
        grpc.channel_ready_future(self._channel).result()
        self.logger.critical('gnes client ready!')

        # create new stub
        self.logger.info('create new stub...')
        self._stub = gnes_pb2_grpc.GnesRPCStub(self._channel)

        # attache response handler
        self.handler._context = self

    def call(self, request):
        resp = self._stub.call(request)
        self.handler.call_routes(resp)
        return resp

    def stream_call(self, request_iterator):
        response_stream = self._stub.StreamCall(request_iterator)
        for resp in response_stream:
            self.handler.call_routes(resp)

    @handler.register(NotImplementedError)
    def _handler_default(self, msg: 'gnes_pb2.Response'):
        raise NotImplementedError

    @handler.register(gnes_pb2.Response)
    def _handler_response_default(self, msg: 'gnes_pb2.Response'):
        pass

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self):
        pass

    def close(self):
        self._channel.close()
        self._stub = None
