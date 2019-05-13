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
from typing import Union, List, Optional, Any

import numpy as np
import zmq

from gnes.proto import gnes_pb2
from zmq.utils import jsonapi

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

class Message:
    prefix_ctrl = 'CTRL_'
    typ_terminate = prefix_ctrl + 'TERMINATE'
    typ_status = prefix_ctrl + 'STATUS'
    typ_default = 'DEFAULT'
    typ_train = 'TRAIN'
    typ_sent_id = 'SENT_ID_MAP'
    typ_doc_id = 'DOC_ID_MAP'

    def __init__(self,
                 client_id: Union[bytes, str] = b'',
                 req_id: Union[bytes, str] = b'',
                 part_id: int = 1,
                 num_part: int = 1,
                 msg_type: Union[bytes, str] = typ_default,
                 msg_content: Any = '',
                 content_type: bytes = b'',
                 route: Union[bytes, str] = b''):
        self._client_id = b''
        self._req_id = b''
        self._msg_type = b''
        self._msg_content = b''
        self._route = b''
        self._content_type = b''
        self._part_id = b''
        self._num_part = b''
        self.client_id = client_id
        self.req_id = req_id
        self.part_id = part_id
        self.num_part = num_part
        self.msg_type = msg_type
        self.content_type = content_type
        self.msg_content = msg_content
        self.route = route

    def to_bytes(self) -> List[bytes]:
        return [self._client_id,
                self._req_id,
                self._part_id,
                self._num_part,
                self._msg_type,
                self._msg_content,
                self._content_type,
                self._route]

    @staticmethod
    def from_bytes(client_id, req_id, part_id, num_part, msg_type, msg_content, content_type, route):
        x = Message()
        x._client_id = client_id
        x._req_id = req_id
        x._part_id = part_id
        x._num_part = num_part
        x._msg_type = msg_type
        x._msg_content = msg_content
        x._content_type = content_type
        x._route = route
        return x

    def copy_mod(self, **kwargs) -> 'Message':
        y = Message()
        y._client_id = self._client_id
        y._req_id = self._req_id
        y._part_id = self._part_id
        y._num_part = self._num_part
        y._msg_type = self._msg_type
        y._msg_content = self._msg_content
        y._route = self._route
        y._content_type = self._content_type
        for k, v in kwargs.items():
            setattr(y, k, v)
        return y

    def __repr__(self):
        return 'client_id: %s, req_id: %s, parts: %d/%d, msg_type: %s, msg_content: %s, route: %s' % \
               (self.client_id, self.req_id, self.part_id, self.num_part, self.msg_type, self.msg_content, self.route)

    @property
    def unique_id(self) -> str:
        return self.client_id + self.req_id

    @property
    def is_control_message(self) -> bool:
        return self.msg_type.startswith(Message.prefix_ctrl)

    @property
    def client_id(self):
        return self._client_id.decode()

    @property
    def part_id(self):
        return _bytes2int(self._part_id)

    @part_id.setter
    def part_id(self, value: int):
        self._part_id = _int2bytes(value)

    @property
    def num_part(self):
        return _bytes2int(self._num_part)

    @num_part.setter
    def num_part(self, value: int):
        self._num_part = _int2bytes(value)

    @client_id.setter
    def client_id(self, value: Union[str, bytes]):
        if not isinstance(value, bytes):
            value = value.encode()
        self._client_id = value

    @property
    def req_id(self):
        return self._req_id.decode()

    @req_id.setter
    def req_id(self, value: Union[str, bytes]):
        if not isinstance(value, bytes):
            value = value.encode()
        self._req_id = value

    @property
    def msg_type(self):
        return self._msg_type.decode()

    @msg_type.setter
    def msg_type(self, value: Union[str, bytes]):
        if not isinstance(value, bytes):
            value = value.encode()
        self._msg_type = value

    @property
    def msg_content(self):
        ct = self.content_type
        if isinstance(ct, dict) and ct['content_type'] == 'array':
            return np.frombuffer(memoryview(self._msg_content), dtype=str(ct['dtype'])).reshape(ct['shape'])
        elif isinstance(ct, dict) and ct['content_type'] == 'map-bytes':
            return ct['id'], self._msg_content
        elif isinstance(ct, dict) and ct['content_type'] == 'map-any':
            return ct['id'], jsonapi.loads(self._msg_content)
        elif isinstance(ct, dict) and ct['content_type'] == 'map-mix':
            return self._msg_content, ct['id'], ct['ex0'], ct['ex1']
        elif ct == 'binary':
            return self._msg_content
        else:
            return jsonapi.loads(self._msg_content)

    @msg_content.setter
    def msg_content(self, value: Any):
        if isinstance(value, np.ndarray):
            self.content_type = dict(content_type='array', dtype=str(value.dtype), shape=value.shape)
            self._msg_content = value
        elif isinstance(value, tuple) and isinstance(value[0], bytes) and len(value) == 4:
            self.content_type = dict(content_type='map-mix', id=value[1],
                                     ex0=value[2], ex1=value[3])
            self._msg_content = value[0]

        elif isinstance(value, bytes):
            self.content_type = 'binary'
            self._msg_content = value
        elif isinstance(value, tuple) and isinstance(value[0], list) and isinstance(value[1], bytes):
            self.content_type = dict(content_type='map-bytes', id=value[0])
            self._msg_content = value[1]
        elif isinstance(value, tuple) and isinstance(value[0], list) and not isinstance(value[1], bytes):
            self.content_type = dict(content_type='map-any', id=value[0])
            self._msg_content = jsonapi.dumps(value[1])
        else:
            self._msg_content = jsonapi.dumps(value)

    @property
    def content_type(self):
        return jsonapi.loads(self._content_type)

    @content_type.setter
    def content_type(self, value: Any):
        if isinstance(value, bytes):
            value = value.decode()
        self._content_type = jsonapi.dumps(value)

    @property
    def route(self):
        return self._route.decode()

    @route.setter
    def route(self, value: Union[str, bytes]):
        if not isinstance(value, bytes):
            value = value.encode()
        self._route = value

def send_message(sock: 'zmq.Socket', msg: 'gnes_pb2.Message', timeout: int = -1) -> None:
    try:
        if timeout > 0:
            sock.setsockopt(zmq.SNDTIMEO, timeout)
        else:
            sock.setsockopt(zmq.SNDTIMEO, -1)

        print(msg.client_id, msg, 'larry - debug')
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
        print(_, msg_data, 'larry-debug-receiv')
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
