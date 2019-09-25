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

import ctypes
import random
from typing import List, Iterator, Tuple
from typing import Optional

import numpy as np
import zmq
from termcolor import colored

from . import gnes_pb2
from ..helper import batch_iterator, default_logger

__all__ = ['RequestGenerator', 'send_message', 'recv_message', 'blob2array', 'array2blob', 'gnes_pb2', 'add_route']


class RequestGenerator:
    @staticmethod
    def index(data: Iterator[bytes], batch_size: int = 0, doc_type: int = gnes_pb2.Document.TEXT,
              doc_id_start: int = 0, request_id_start: int = 0,
              random_doc_id: bool = False,
              *args, **kwargs):

        for pi in batch_iterator(data, batch_size):
            req = gnes_pb2.Request()
            req.request_id = request_id_start
            for raw_bytes in pi:
                d = req.index.docs.add()
                d.doc_id = doc_id_start if not random_doc_id else random.randint(0, ctypes.c_uint(-1).value)
                d.raw_bytes = raw_bytes
                d.weight = 1.0
                d.doc_type = doc_type
                doc_id_start += 1
            yield req
            request_id_start += 1

    @staticmethod
    def train(data: Iterator[bytes], batch_size: int = 0, doc_type: int = gnes_pb2.Document.TEXT,
              doc_id_start: int = 0, request_id_start: int = 0,
              random_doc_id: bool = False,
              *args, **kwargs):
        for pi in batch_iterator(data, batch_size):
            req = gnes_pb2.Request()
            req.request_id = request_id_start
            for raw_bytes in pi:
                d = req.train.docs.add()
                d.doc_id = doc_id_start if not random_doc_id else random.randint(0, ctypes.c_uint(-1).value)
                d.raw_bytes = raw_bytes
                d.doc_type = doc_type
                if not random_doc_id:
                    doc_id_start += 1
            yield req
            request_id_start += 1
        req = gnes_pb2.Request()
        req.request_id = request_id_start
        req.train.flush = True
        yield req
        request_id_start += 1

    @staticmethod
    def query(query: bytes, top_k: int, request_id_start: int = 0, doc_type: int = gnes_pb2.Document.TEXT, *args,
              **kwargs):
        if top_k <= 0:
            raise ValueError('"top_k: %d" is not a valid number' % top_k)

        req = gnes_pb2.Request()
        req.request_id = request_id_start
        req.search.query.raw_bytes = query
        req.search.query.doc_type = doc_type
        req.search.top_k = top_k
        yield req


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


def router2str(m: 'gnes_pb2.Message') -> str:
    route_str = [r.service for r in m.envelope.routes]
    return colored('▸', 'green').join(route_str)


def add_route(evlp: 'gnes_pb2.Envelope', name: str, identity: str):
    r = evlp.routes.add()
    r.service = name
    r.start_time.GetCurrentTime()
    r.service_identity = identity


def merge_routes(msg: 'gnes_pb2.Message', prev_msgs: List['gnes_pb2.Message']):
    # take unique routes by service identity
    routes = {(r.service + r.service_identity): r for m in prev_msgs for r in m.envelope.routes}
    msg.envelope.ClearField('routes')
    msg.envelope.routes.extend(sorted(routes.values(), key=lambda x: (x.start_time.seconds, x.start_time.nanos)))


def check_msg_version(msg: 'gnes_pb2.Message'):
    from .. import __version__, __proto_version__
    if hasattr(msg.envelope, 'gnes_version'):
        if not msg.envelope.gnes_version:
            # only happen in unittest
            default_logger.warning('incoming message contains empty "gnes_version", '
                                   'you may ignore it in debug/unittest mode. '
                                   'otherwise please check if frontend service set correct version')
        elif __version__ != msg.envelope.gnes_version:
            raise AttributeError('mismatched GNES version! '
                                 'incoming message has GNES version %s, whereas local GNES version %s' % (
                                     msg.envelope.gnes_version, __version__))

    if hasattr(msg.envelope, 'proto_version'):
        if not msg.envelope.proto_version:
            # only happen in unittest
            default_logger.warning('incoming message contains empty "proto_version", '
                                   'you may ignore it in debug/unittest mode. '
                                   'otherwise please check if frontend service set correct version')
        elif __proto_version__ != msg.envelope.proto_version:
            raise AttributeError('mismatched protobuf version! '
                                 'incoming message has protobuf version %s, whereas local protobuf version %s' % (
                                     msg.envelope.proto_version, __proto_version__))

    if not hasattr(msg.envelope, 'proto_version') and not hasattr(msg.envelope, 'gnes_version'):
        raise AttributeError('version_check=True locally, '
                             'but incoming message contains no version info in its envelope. '
                             'the message is probably sent from a very outdated GNES version')


def extract_raw_bytes_from_msg(msg: 'gnes_pb2.Message') -> Tuple[Optional[List[bytes]], Optional[List[bytes]]]:
    doc_bytes = [msg.envelope.client_id.encode()]
    chunk_bytes = [msg.envelope.client_id.encode()]

    # for train request
    for d in msg.request.train.docs:
        doc_bytes.append(d.raw_bytes)
        d.ClearField('raw_bytes')
        for c in d.chunks:
            chunk_bytes.append(c.raw)
            c.ClearField('raw')

    # for index request
    for d in msg.request.index.docs:
        doc_bytes.append(d.raw_bytes)
        d.ClearField('raw_bytes')
        for c in d.chunks:
            chunk_bytes.append(c.raw)
            c.ClearField('raw')

    # for query
    if msg.request.search.query.raw_bytes:
        doc_bytes.append(msg.request.search.query.raw_bytes)
        msg.request.search.query.ClearField('raw_bytes')

    for c in msg.request.search.query.chunks:
        chunk_bytes.append(c.raw)
        c.ClearField('raw')

    return doc_bytes, chunk_bytes


def fill_raw_bytes_to_msg(msg: 'gnes_pb2.Message', doc_raw_bytes: Optional[List[bytes]],
                          chunk_raw_bytes: Optional[List[bytes]]):
    c_idx = 0
    d_idx = 0
    for d in msg.request.train.docs:
        if doc_raw_bytes and doc_raw_bytes[d_idx]:
            d.raw_bytes = doc_raw_bytes[d_idx]
        d_idx += 1
        for c in d.chunks:
            if chunk_raw_bytes and chunk_raw_bytes[c_idx]:
                c.raw = chunk_raw_bytes[c_idx]
            c_idx += 1


def send_message(sock: 'zmq.Socket', msg: 'gnes_pb2.Message', timeout: int = -1,
                 raw_bytes_in_separate: bool = False, **kwargs) -> None:
    try:
        if timeout > 0:
            sock.setsockopt(zmq.SNDTIMEO, timeout)
        else:
            sock.setsockopt(zmq.SNDTIMEO, -1)

        if not raw_bytes_in_separate:
            sock.send_multipart([msg.envelope.client_id.encode(), b'0', msg.SerializeToString()])
        else:
            doc_bytes, chunk_bytes = extract_raw_bytes_from_msg(msg)
            # now raw_bytes are removed from message, hoping for faster de/serialization
            sock.send_multipart(
                [msg.envelope.client_id.encode(),
                 b'1', msg.SerializeToString(),
                 b'%d' % len(doc_bytes), *doc_bytes,
                 b'%d' % len(chunk_bytes), *chunk_bytes])
    except zmq.error.Again:
        raise TimeoutError(
            'cannot send message to sock %s after timeout=%dms, please check the following:'
            'is the server still online? is the network broken? are "port" correct? ' % (
                sock, timeout))
    except Exception as ex:
        raise ex
    finally:
        sock.setsockopt(zmq.SNDTIMEO, -1)


def recv_message(sock: 'zmq.Socket', timeout: int = -1, check_version: bool = False, **kwargs) -> Optional[
    'gnes_pb2.Message']:
    response = []
    try:
        if timeout > 0:
            sock.setsockopt(zmq.RCVTIMEO, timeout)
        else:
            sock.setsockopt(zmq.RCVTIMEO, -1)

        msg = gnes_pb2.Message()
        msg_data = sock.recv_multipart()
        raw_bytes_in_separate = (msg_data[1] == b'1')
        msg.ParseFromString(msg_data[2])

        if check_version:
            check_msg_version(msg)

        # now we have a barebone msg, we need to fill in data
        if raw_bytes_in_separate:
            doc_bytes_len_pos = 3
            doc_bytes_len = int(msg_data[doc_bytes_len_pos])
            doc_bytes = msg_data[(doc_bytes_len_pos + 1):(doc_bytes_len_pos + 1 + doc_bytes_len)]
            chunk_bytes_len_pos = doc_bytes_len_pos + 1 + doc_bytes_len
            chunk_bytes_len = int(msg_data[chunk_bytes_len_pos])
            chunk_bytes = msg_data[(chunk_bytes_len_pos + 1):]
            if len(chunk_bytes) != chunk_bytes_len:
                raise ValueError('"chunk_bytes_len"=%d in message, but the actual length is %d' % (
                    chunk_bytes_len, len(chunk_bytes)))
            fill_raw_bytes_to_msg(msg, doc_bytes, chunk_bytes)
        return msg

    except ValueError:
        raise ValueError('received a wrongly-formatted request (expected 4 frames, got %d)' % len(response))
    except zmq.error.Again:
        raise TimeoutError(
            'no response from sock %s after timeout=%dms, please check the following:'
            'is the server still online? is the network broken? are "port" correct? ' % (
                sock, timeout))
    except Exception as ex:
        raise ex
    finally:
        sock.setsockopt(zmq.RCVTIMEO, -1)
