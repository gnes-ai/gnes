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

import uuid

import numpy as np

from . import gnes_pb2

__all__ = ['blob2array', 'array2blob', 'new_message', 'gnes_pb2']


def blob2array(blob: 'gnes_pb2.NdArray') -> np.ndarray:
    """
    Convert a blob proto to an array.
    """
    return np.frombuffer(blob.data, dtype=blob.dtype).reshape(blob.shape)


def array2blob(x: np.ndarray) -> 'gnes_pb2.NdArray':
    """Converts a N-dimensional array to blob proto.
    """
    blob = gnes_pb2.NdArray()
    blob.data = x.tobytes()
    blob.shape.extend(list(x.shape))
    blob.dtype = x.dtype.name
    return blob


def new_message(client_id: str,
                request_id: str = str(uuid.uuid4()),
                num_part: int = 1,
                part_id: int = 1,
                timeout: int = 5000) -> 'gnes_pb2.BaseMessage':
    msg = gnes_pb2.BaseMessage()
    # make an envelope
    msg.envelope.client_id = client_id
    msg.envelope.request_id = request_id
    r = msg.envelope.routes.add()
    r.service = client_id
    r.timestamp.GetCurrentTime()
    msg.envelope.part_id = part_id
    msg.envelope.num_part = num_part
    msg.envelope.timeout = timeout
    return msg
