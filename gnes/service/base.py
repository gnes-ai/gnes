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


import threading
import time
import types
from enum import Enum
from typing import Tuple, List, Union, Type

import zmq
import zmq.decorators as zmqd
from termcolor import colored

from ..base import TrainableBase, T
from ..helper import set_logger
from ..proto import gnes_pb2, add_route, send_message, recv_message


class BetterEnum(Enum):
    def __str__(self):
        return self.name

    @classmethod
    def from_string(cls, s):
        try:
            return cls[s]
        except KeyError:
            raise ValueError()


class ReduceOp(BetterEnum):
    CONCAT = 0
    ALWAYS_ONE = 1


class SocketType(BetterEnum):
    PULL_BIND = 0
    PULL_CONNECT = 1
    PUSH_BIND = 2
    PUSH_CONNECT = 3
    SUB_BIND = 4
    SUB_CONNECT = 5
    PUB_BIND = 6
    PUB_CONNECT = 7
    PAIR_BIND = 8
    PAIR_CONNECT = 9

    @property
    def is_bind(self):
        return self.value % 2 == 0


class BlockMessage(Exception):
    pass


class ComponentNotLoad(Exception):
    pass


class ServiceError(Exception):
    pass


class EventLoopEnd(Exception):
    pass


def build_socket(ctx: 'zmq.Context', host: str, port: int, socket_type: 'SocketType', identity: 'str' = None) -> Tuple[
    'zmq.Socket', str]:
    sock = {
        SocketType.PULL_BIND: lambda: ctx.socket(zmq.PULL),
        SocketType.PULL_CONNECT: lambda: ctx.socket(zmq.PULL),
        SocketType.SUB_BIND: lambda: ctx.socket(zmq.SUB),
        SocketType.SUB_CONNECT: lambda: ctx.socket(zmq.SUB),
        SocketType.PUB_BIND: lambda: ctx.socket(zmq.PUB),
        SocketType.PUB_CONNECT: lambda: ctx.socket(zmq.PUB),
        SocketType.PUSH_BIND: lambda: ctx.socket(zmq.PUSH),
        SocketType.PUSH_CONNECT: lambda: ctx.socket(zmq.PUSH),
        SocketType.PAIR_BIND: lambda: ctx.socket(zmq.PAIR),
        SocketType.PAIR_CONNECT: lambda: ctx.socket(zmq.PAIR)
    }[socket_type]()

    if socket_type.is_bind:
        if port is None:
            sock.bind_to_random_port('tcp://%s' % host)
        else:
            sock.bind('tcp://%s:%d' % (host, port))
    else:
        if port is None:
            sock.connect(host)
        else:
            sock.connect('tcp://%s:%d' % (host, port))

    if socket_type in {SocketType.SUB_CONNECT, SocketType.SUB_BIND}:
        sock.setsockopt(zmq.SUBSCRIBE, identity.encode('ascii') if identity else b'')
        # sock.setsockopt(zmq.SUBSCRIBE, b'')

    return sock, sock.getsockopt_string(zmq.LAST_ENDPOINT)


class MessageHandler:
    def __init__(self, mh: 'MessageHandler' = None):
        self.routes = {k: v for k, v in mh.routes.items()} if mh else {}
        self.logger = set_logger(self.__class__.__name__)

    def register(self, msg_type: Union[List, Tuple, type]):
        def decorator(f):
            if isinstance(msg_type, list) or isinstance(msg_type, tuple):
                for m in msg_type:
                    self.routes[m] = f
            else:
                self.routes[msg_type] = f
            return f

        return decorator

    def serve(self, msg: 'gnes_pb2.Message'):
        def get_default_fn(m_type):
            self.logger.warning('cant find handler for message type: %s, fall back to the default handler' % m_type)
            f = self.routes.get(m_type, self.routes[NotImplementedError])
            return f

        if msg.WhichOneof('body'):
            body = getattr(msg, msg.WhichOneof('body'))
            if body.WhichOneof('body'):
                msg_type = type(getattr(body, body.WhichOneof('body')))
                if msg_type in self.routes:
                    self.logger.info('received a %r message' % msg_type.__name__)
                    fn = self.routes.get(msg_type)
                else:
                    fn = get_default_fn(msg_type)
            else:
                fn = get_default_fn(type(body))
        else:
            fn = get_default_fn(type(msg))
        return fn


class BaseService(threading.Thread):
    handler = MessageHandler()
    default_host = '0.0.0.0'

    def __init__(self, args, use_event_loop=True):
        super().__init__()
        self.args = args
        self.logger = set_logger(self.__class__.__name__, self.args.verbose)
        self.is_ready = threading.Event()
        self.is_event_loop = threading.Event()
        self.is_model_changed = threading.Event()
        self.is_handler_done = threading.Event()
        self._model = None
        self.identity = args.identity if 'identity' in args else None
        self.use_event_loop = use_event_loop

    def run(self):
        self._run()

    def _start_auto_dump(self):
        if self.args.dump_interval > 0 and not self.args.read_only:
            self._auto_dump_thread = threading.Thread(target=self._auto_dump)
            self._auto_dump_thread.setDaemon(1)
            self._auto_dump_thread.start()

    def _auto_dump(self):
        while self.is_event_loop.is_set():
            if self.is_model_changed.is_set():
                self.is_model_changed.clear()
                self.logger.info(
                    'auto-dumping the new change of the model every %ds...' % self.args.dump_interval)
                self.dump()
                time.sleep(self.args.dump_interval)
            else:
                time.sleep(1)

    def dump(self):
        if not self.args.read_only:
            if self._model:
                self.logger.info('dumping changes to the model...')
                self._model.dump(self.args.dump_path)
                self.logger.info('dumping finished!')
        else:
            self.logger.warning('dumping is not allowed as "read_only" is set to true.')

    def message_handler(self, msg: 'gnes_pb2.Message'):
        try:
            fn = self.handler.serve(msg)
            if fn:
                add_route(msg.envelope, '%s:%s' % (self.__class__.__name__, self._model.__class__.__name__))
                self.logger.info(
                    'handling a message with route: %s' % '->'.join([r.service for r in msg.envelope.routes]))
                if msg.request and msg.request.WhichOneof('body') and \
                        type(getattr(msg.request, msg.request.WhichOneof('body'))) == gnes_pb2.Request.ControlRequest:
                    out_sock = self.ctrl_sock
                else:
                    out_sock = self.out_sock
                try:
                    # NOTE that msg is mutable object, it may be modified in fn()
                    ret = fn(self, msg)
                    if ret is None:
                        # assume 'msg' is modified inside fn()
                        send_message(out_sock, msg, timeout=self.args.timeout)
                    elif isinstance(ret, types.GeneratorType):
                        for r_msg in ret:
                            send_message(out_sock, r_msg, timeout=self.args.timeout)
                    else:
                        raise ServiceError('unknown return type from the handler: %s' % fn)

                    self.logger.info('handler %s is done' % fn.__name__)
                except BlockMessage:
                    pass
                except EventLoopEnd:
                    send_message(out_sock, msg, timeout=self.args.timeout)
                    raise EventLoopEnd
        except ServiceError as e:
            self.logger.error(e)

    def send_message(self, *args, **kwargs):
        send_message(self.out_sock, *args, **kwargs)

    def recv_message(self, *args, **kwargs):
        m = recv_message(self.in_sock, *args, **kwargs)
        self.is_handler_done.set()
        return m

    @zmqd.context()
    def _run(self, ctx):
        ctx.setsockopt(zmq.LINGER, 0)
        self.logger.info('bind sockets...')
        in_sock, _ = build_socket(ctx, self.args.host_in, self.args.port_in, self.args.socket_in,
                                  getattr(self, 'identity', None))
        out_sock, _ = build_socket(ctx, self.args.host_out, self.args.port_out, self.args.socket_out,
                                   getattr(self, 'identity', None))
        ctrl_sock, self.ctrl_addr = build_socket(ctx, self.default_host, self.args.port_ctrl, SocketType.PAIR_BIND)
        self.in_sock, self.out_sock, self.ctrl_sock = in_sock, out_sock, ctrl_sock

        self.logger.info(
            'input %s:%s\t output %s:%s\t control over %s' % (
                self.args.host_in, colored(self.args.port_in, 'yellow'),
                self.args.host_out, colored(self.args.port_out, 'yellow'),
                colored(self.ctrl_addr, 'yellow')))

        poller = zmq.Poller()
        poller.register(in_sock, zmq.POLLIN)
        poller.register(ctrl_sock, zmq.POLLIN)

        try:
            self.post_init()
            self.is_ready.set()
            self.is_event_loop.set()
            self._start_auto_dump()
            self.logger.info('ready and listening')
            while self.is_event_loop.is_set():
                pull_sock = None
                socks = dict(poller.poll())
                if socks.get(in_sock) == zmq.POLLIN:
                    pull_sock = in_sock
                elif socks.get(ctrl_sock) == zmq.POLLIN:
                    pull_sock = ctrl_sock
                else:
                    self.logger.error('received message from unknown socket: %s' % socks)
                if self.use_event_loop or pull_sock == ctrl_sock:
                    self.is_handler_done.clear()
                    msg = recv_message(pull_sock)
                    self.message_handler(msg)
                    self.is_handler_done.set()
                else:
                    self.logger.warning(
                        'received a new message but since "use_event_loop=False" I will not handle it. '
                        'I will just block the thread until "is_handler_done" is set!')
                    self.is_handler_done.wait()
                    self.is_handler_done.clear()
                if self.args.dump_interval == 0:
                    self.dump()
        except EventLoopEnd:
            self.logger.info('break from the event loop')
        except ComponentNotLoad:
            self.logger.error('component can not be correctly loaded, terminated')
        finally:
            self.is_ready.set()
            self.is_event_loop.clear()
            self.in_sock.close()
            self.out_sock.close()
            self.ctrl_sock.close()
        self.logger.info('terminated')

    def post_init(self):
        pass

    def load_model(self, base_class: Type[TrainableBase]) -> T:
        try:
            model = base_class.load(self.args.dump_path)
            self.logger.info(
                'load a trained %s from a binary file: %s' % (model.__class__.__name__, self.args.dump_path))
        except FileNotFoundError:
            self.logger.warning('fail to load the model from %s' % self.args.dump_path)
            try:
                model = base_class.load_yaml(self.args.yaml_path)
                self.logger.warning('load an empty %s from %s' % (model.__class__.__name__, self.args.yaml_path))
            except FileNotFoundError:
                raise ComponentNotLoad
        return model

    @handler.register(NotImplementedError)
    def _handler_default(self, msg: 'gnes_pb2.Message'):
        raise NotImplementedError

    @handler.register(gnes_pb2.Request.ControlRequest)
    def _handler_control(self, msg: 'gnes_pb2.Message'):
        if msg.request.control.command == gnes_pb2.Request.ControlRequest.TERMINATE:
            self.is_event_loop.clear()
            msg.response.control.status = gnes_pb2.Response.SUCCESS
            raise EventLoopEnd
        elif msg.request.control.command == gnes_pb2.Request.ControlRequest.STATUS:
            msg.response.control.status = gnes_pb2.Response.ERROR
        else:
            raise ServiceError('dont know how to handle %s' % msg.request.control)

    def close(self):
        if self._model:
            self.dump()
            self._model.close()

        if self.is_event_loop.is_set():
            msg = gnes_pb2.Message()
            msg.request.control.command = gnes_pb2.Request.ControlRequest.TERMINATE
            return send_ctrl_message(self.ctrl_addr, msg, timeout=self.args.timeout)

    @property
    def status(self):
        msg = gnes_pb2.Message()
        msg.request.control.command = gnes_pb2.Request.ControlRequest.STATUS
        return send_ctrl_message(self.ctrl_addr, msg, timeout=self.args.timeout)

    def __enter__(self):
        self.start()
        self.is_ready.wait()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def send_ctrl_message(address: str, msg: 'gnes_pb2.Message', timeout: int):
    # control message is short, set a timeout and ask for quick response
    with zmq.Context() as ctx:
        ctx.setsockopt(zmq.LINGER, 0)
        sock, _ = build_socket(ctx, address, None, SocketType.PAIR_CONNECT)
        send_message(sock, msg, timeout)
        r = recv_message(sock, timeout)
        sock.close()
        return r
