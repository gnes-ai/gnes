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
import os
import random
from typing import List, Iterator, Tuple
from typing import Optional

import numpy as np
import zmq
from termcolor import colored

from . import gnes_pb2
from ..helper import batch_iterator, default_logger

__all__ = ['RequestGenerator', 'send_message', 'recv_message',
           'blob2array', 'array2blob', 'gnes_pb2', 'add_route', 'add_version']


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
    x = np.frombuffer(blob.data, dtype=blob.dtype).copy()
    return x.reshape(blob.shape)


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


def add_version(evlp: 'gnes_pb2.Envelope'):
    from .. import __version__, __proto_version__
    evlp.gnes_version = __version__
    evlp.proto_version = __proto_version__
    evlp.vcs_version = os.environ.get('GNES_VCS_VERSION', '')


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

    if hasattr(msg.envelope, 'vcs_version'):
        if not msg.envelope.vcs_version or not os.environ.get('GNES_VCS_VERSION'):
            default_logger.warning('incoming message contains empty "vcs_version", '
                                   'you may ignore it in debug/unittest mode, '
                                   'or if you run gnes OUTSIDE docker container where GNES_VCS_VERSION is unset'
                                   'otherwise please check if frontend service set correct version')
        elif os.environ.get('GNES_VCS_VERSION') != msg.envelope.vcs_version:
            raise AttributeError('mismatched vcs version! '
                                 'incoming message has vcs_version %s, whereas local environment vcs_version is %s' % (
                                     msg.envelope.vcs_version, os.environ.get('GNES_VCS_VERSION')))

    if not hasattr(msg.envelope, 'proto_version') and not hasattr(msg.envelope, 'gnes_version'):
        raise AttributeError('version_check=True locally, '
                             'but incoming message contains no version info in its envelope. '
                             'the message is probably sent from a very outdated GNES version')


def extract_bytes_from_msg(msg: 'gnes_pb2.Message') -> Tuple:
    doc_bytes = []
    chunk_bytes = []
    doc_byte_type = b''
    chunk_byte_type = b''

    docs = msg.request.train.docs or msg.request.index.docs or [msg.request.search.query]
    # for train request
    for d in docs:
        # oneof raw_data {
        #     string raw_text = 5;
        #       NdArray raw_image = 6;
        #       NdArray raw_video = 7;
        #       bytes raw_bytes = 8; // for other types
        # }
        dtype = d.WhichOneof('raw_data') or ''
        doc_byte_type = dtype.encode()
        if dtype == 'raw_bytes':
            doc_bytes.append(d.raw_bytes)
            d.ClearField('raw_bytes')
        elif dtype == 'raw_image':
            doc_bytes.append(d.raw_image.data)
            d.raw_image.ClearField('data')
        elif dtype == 'raw_video':
            doc_bytes.append(d.raw_video.data)
            d.raw_video.ClearField('data')
        elif dtype == 'raw_text':
            doc_bytes.append(d.raw_text.encode())
            d.ClearField('raw_text')

        for c in d.chunks:
            # oneof content {
            # string text = 2;
            # NdArray blob = 3;
            # bytes raw = 7;
            # }
            chunk_bytes.append(c.embedding.data)
            c.embedding.ClearField('data')

            ctype = c.WhichOneof('content') or ''
            chunk_byte_type = ctype.encode()
            if ctype == 'raw':
                chunk_bytes.append(c.raw)
                c.ClearField('raw')
            elif ctype == 'blob':
                chunk_bytes.append(c.blob.data)
                c.blob.ClearField('data')
            elif ctype == 'text':
                chunk_bytes.append(c.text.encode())
                c.ClearField('text')

    return doc_bytes, doc_byte_type, chunk_bytes, chunk_byte_type


def fill_raw_bytes_to_msg(msg: 'gnes_pb2.Message', msg_data: List[bytes]):
    doc_byte_type = msg_data[2].decode()
    chunk_byte_type = msg_data[3].decode()
    doc_bytes_len = int(msg_data[4])
    chunk_bytes_len = int(msg_data[5])

    doc_bytes = msg_data[6:(6 + doc_bytes_len)]
    chunk_bytes = msg_data[(6 + doc_bytes_len):]

    if len(chunk_bytes) != chunk_bytes_len:
        raise ValueError('"chunk_bytes_len"=%d in message, but the actual length is %d' % (
            chunk_bytes_len, len(chunk_bytes)))

    c_idx = 0
    d_idx = 0
    docs = msg.request.train.docs or msg.request.index.docs or [msg.request.search.query]
    for d in docs:
        if doc_bytes and doc_bytes[d_idx]:
            if doc_byte_type == 'raw_bytes':
                d.raw_bytes = doc_bytes[d_idx]
                d_idx += 1
            elif doc_byte_type == 'raw_image':
                d.raw_image.data = doc_bytes[d_idx]
                d_idx += 1
            elif doc_byte_type == 'raw_video':
                d.raw_video.data = doc_bytes[d_idx]
                d_idx += 1
            elif doc_byte_type == 'raw_text':
                d.raw_text = doc_bytes[d_idx].decode()
                d_idx += 1

        for c in d.chunks:
            if chunk_bytes and chunk_bytes[c_idx]:
                c.embedding.data = chunk_bytes[c_idx]
            c_idx += 1

            if chunk_byte_type == 'raw':
                c.raw = chunk_bytes[c_idx]
                c_idx += 1
            elif chunk_byte_type == 'blob':
                c.blob.data = chunk_bytes[c_idx]
                c_idx += 1
            elif chunk_byte_type == 'text':
                c.text = chunk_bytes[c_idx].decode()
                c_idx += 1


def send_message(sock: 'zmq.Socket', msg: 'gnes_pb2.Message', timeout: int = -1,
                 squeeze_pb: bool = False, **kwargs) -> None:
    try:
        if timeout > 0:
            sock.setsockopt(zmq.SNDTIMEO, timeout)
        else:
            sock.setsockopt(zmq.SNDTIMEO, -1)

        if not squeeze_pb:
            sock.send_multipart([msg.envelope.client_id.encode(), msg.SerializeToString()])
        else:
            doc_bytes, doc_byte_type, chunk_bytes, chunk_byte_type = extract_bytes_from_msg(msg)
            # now raw_bytes are removed from message, hoping for faster de/serialization
            sock.send_multipart(
                [msg.envelope.client_id.encode(),  # 0
                 msg.SerializeToString(),  # 1
                 doc_byte_type, chunk_byte_type,  # 2, 3
                 b'%d' % len(doc_bytes), b'%d' % len(chunk_bytes),  # 4, 5
                 *doc_bytes, *chunk_bytes])  # 6, 7
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
    try:
        if timeout > 0:
            sock.setsockopt(zmq.RCVTIMEO, timeout)
        else:
            sock.setsockopt(zmq.RCVTIMEO, -1)

        msg = gnes_pb2.Message()
        msg_data = sock.recv_multipart()
        msg.ParseFromString(msg_data[1])
        if check_version:
            check_msg_version(msg)

        # now we have a barebone msg, we need to fill in data
        if len(msg_data) > 2:
            fill_raw_bytes_to_msg(msg, msg_data)
        return msg

    except zmq.error.Again:
        raise TimeoutError(
            'no response from sock %s after timeout=%dms, please check the following:'
            'is the server still online? is the network broken? are "port" correct? ' % (
                sock, timeout))
    except Exception as ex:
        raise ex
    finally:
        sock.setsockopt(zmq.RCVTIMEO, -1)
