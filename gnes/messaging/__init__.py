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


from enum import Enum
from typing import Optional

import zmq

from gnes.proto import gnes_pb2

__all__ = ['MessageType', 'send_message', 'recv_message']


class MessageType(Enum):
    def __str__(self):
        return self.name

    CTRL_TERMINATE = 1
    CTRL_STATUS = 2
    DEFAULT = 3
    TRAIN = 4

    @classmethod
    def is_control_message(cls, typ_name) -> bool:
        return typ_name.startswith('CTRL_')


def send_message(sock: 'zmq.Socket', msg: 'gnes_pb2.Message', timeout: int = -1) -> None:
    try:
        if timeout > 0:
            sock.setsockopt(zmq.SNDTIMEO, timeout)
        else:
            sock.setsockopt(zmq.SNDTIMEO, -1)

        sock.send_multipart([msg.client_id.encode(), msg.SerializeToString()])
    except zmq.error.Again:
        raise TimeoutError(
            'no response from sock %s after timeout=%dms, please check the following:'
            'is the server still online? is the network broken? are "port" correct? ' % (
                sock, timeout))
    finally:
        sock.setsockopt(zmq.SNDTIMEO, -1)


def recv_message(sock: 'zmq.Socket', timeout: int = -1) -> Optional['gnes_pb2.Message']:
    response = []
    try:
        if timeout > 0:
            sock.setsockopt(zmq.RCVTIMEO, timeout)
        else:
            sock.setsockopt(zmq.RCVTIMEO, -1)
        _, msg_data = sock.recv_multipart()
        msg = gnes_pb2.Message()
        msg.ParseFromString(msg_data)
        return msg

    except ValueError:
        raise ValueError('received a wrongly-formatted request (expected 4 frames, got %d)' % len(response))
    except zmq.error.Again:
        raise TimeoutError(
            'no response from sock %s after timeout=%dms, please check the following:'
            'is the server still online? is the network broken? are "port" correct? ' % (
                sock, timeout))
    finally:
        sock.setsockopt(zmq.RCVTIMEO, -1)
