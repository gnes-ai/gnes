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


import zmq

from ..helper import set_logger
from ..proto import send_message, gnes_pb2, recv_message
from ..service.base import build_socket


class ZmqClient:

    def __init__(self, args):
        self.args = args
        self.identity = args.identity if 'identity' in args else None
        self.logger = set_logger(self.__class__.__name__, self.args.verbose)
        self.ctx = zmq.Context()
        self.ctx.setsockopt(zmq.LINGER, 0)
        self.receiver, recv_addr = build_socket(self.ctx, self.args.host_in, self.args.port_in, self.args.socket_in,
                                                getattr(self, 'identity', None))
        self.sender, send_addr = build_socket(self.ctx, self.args.host_out, self.args.port_out, self.args.socket_out,
                                              getattr(self, 'identity', None))
        self.logger.info('send via %s, receive via %s' % (send_addr, recv_addr))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.sender.close()
        self.receiver.close()
        self.ctx.term()

    def send_message(self, message: "gnes_pb2.Message", timeout: int = -1):
        send_message(self.sender, message, timeout=timeout)

    def recv_message(self, timeout: int = -1) -> gnes_pb2.Message:
        return recv_message(self.receiver, timeout=timeout)
