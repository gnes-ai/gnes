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

import copy
import multiprocessing
import random
import threading
import time
import types
from contextlib import ExitStack
from enum import Enum
from typing import Tuple, List, Union, Type

import zmq
import zmq.decorators as zmqd
from termcolor import colored

from ..base import TrainableBase, T
from ..cli.parser import resolve_yaml_path
from ..helper import set_logger, PathImporter, TimeContext, make_route_table
from ..proto import gnes_pb2, add_route, send_message, recv_message, router2str


class BetterEnum(Enum):
    def __str__(self):
        return self.name

    @classmethod
    def from_string(cls, s):
        try:
            return cls[s]
        except KeyError:
            raise ValueError('%s is not a valid enum for %s' % (s, cls))


class ReduceOp(BetterEnum):
    CONCAT = 0
    ALWAYS_ONE = 1


class ParallelType(BetterEnum):
    PUSH_BLOCK = 0
    PUSH_NONBLOCK = 1
    PUB_BLOCK = 2
    PUB_NONBLOCK = 3

    @property
    def is_push(self):
        return self.value == 0 or self.value == 1

    @property
    def is_block(self):
        return self.value == 0 or self.value == 2


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

    @property
    def paired(self):
        return {
            SocketType.PULL_BIND: SocketType.PUSH_CONNECT,
            SocketType.PULL_CONNECT: SocketType.PUSH_BIND,
            SocketType.SUB_BIND: SocketType.PUB_CONNECT,
            SocketType.SUB_CONNECT: SocketType.PUB_BIND,
            SocketType.PAIR_BIND: SocketType.PAIR_CONNECT,
            SocketType.PUSH_CONNECT: SocketType.PULL_BIND,
            SocketType.PUSH_BIND: SocketType.PULL_CONNECT,
            SocketType.PUB_CONNECT: SocketType.SUB_BIND,
            SocketType.PUB_BIND: SocketType.SUB_CONNECT,
            SocketType.PAIR_CONNECT: SocketType.PAIR_BIND
        }[self]


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
        host = BaseService.default_host
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

    # Note: the following very dangerous for pub-sub socketc
    sock.setsockopt(zmq.RCVHWM, 10)
    sock.setsockopt(zmq.RCVBUF, 10 * 1024 * 1024)  # limit of network buffer 100M

    sock.setsockopt(zmq.SNDHWM, 10)
    sock.setsockopt(zmq.SNDBUF, 10 * 1024 * 1024)  # limit of network buffer 100M

    return sock, sock.getsockopt_string(zmq.LAST_ENDPOINT)


class MessageHandler:
    def __init__(self, mh: 'MessageHandler' = None):
        self.routes = {}
        self.hooks = {'pre': [], 'post': []}

        if mh:
            self.routes = copy.deepcopy(mh.routes)
            self.hooks = copy.deepcopy(mh.hooks)

        self.logger = set_logger(self.__class__.__name__)
        self.service_context = None

    def register(self, msg_type: Union[List, Tuple, type]):
        def decorator(f):
            if isinstance(msg_type, list) or isinstance(msg_type, tuple):
                for m in msg_type:
                    self.routes[m] = f.__name__
            else:
                self.routes[msg_type] = f.__name__
            return f

        return decorator

    def register_hook(self, hook_type: Union[str, Tuple[str]], only_when_verbose: bool = False):
        """
        Register a function as a pre/post hook

        :param only_when_verbose: only call the hook when verbose is true
        :param hook_type: possible values 'pre' or 'post' or ('pre', 'post')
        """

        def decorator(f):
            if isinstance(hook_type, str) and hook_type in self.hooks:
                self.hooks[hook_type].append((f.__name__, only_when_verbose))
                return f
            elif isinstance(hook_type, list) or isinstance(hook_type, tuple):
                for h in set(hook_type):
                    if h in self.hooks:
                        self.hooks[h].append((f.__name__, only_when_verbose))
                    else:
                        raise AttributeError('hook type: %s is not supported' % h)
                return f
            else:
                raise TypeError('hook_type is in bad type: %s' % type(hook_type))

        return decorator

    def call_hooks(self, msg: 'gnes_pb2.Message', hook_type: Union[str, Tuple[str]], *args, **kwargs):
        """
        All post handler hooks are called after the handler is done but before
        sending out the message to the next service.
        All pre handler hooks are called after the service received a message
        and before calling the message handler
        """
        hooks = []
        if isinstance(hook_type, str) and hook_type in self.hooks:
            hooks.extend(self.hooks[hook_type])
        elif isinstance(hook_type, list) or isinstance(hook_type, tuple):
            for h in set(hook_type):
                if h in self.hooks:
                    hooks.extend(self.hooks[h])
                else:
                    raise AttributeError('hook type: %s is not supported' % h)
        else:
            raise TypeError('hook_type is in bad type: %s' % type(hook_type))

        for fn, only_verbose in hooks:
            if (only_verbose and self.service_context.args.verbose) or (not only_verbose):
                try:
                    fn(msg, *args, **kwargs)
                except Exception as ex:
                    self.logger.warning('hook %s throws an exception, '
                                        'this wont affect the server but you may want to pay attention' % fn)
                    self.logger.error(ex, exc_info=True)

    def call_routes(self, msg: 'gnes_pb2.Message'):
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

        self.logger.info('handling message with %s' % fn.__name__)
        return fn(msg)

    def call_routes_send_back(self, msg: 'gnes_pb2.Message', out_sock):
        try:
            # NOTE that msg is mutable object, it may be modified in fn()
            ret = self.call_routes(msg)
            if ret is None:
                # assume 'msg' is modified inside fn()
                self.call_hooks(msg, hook_type='post', verbose=self.service_context.args.verbose)
                send_message(out_sock, msg, **self.service_context.send_recv_kwargs)
            elif isinstance(ret, types.GeneratorType):
                for r_msg in ret:
                    self.call_hooks(msg, hook_type='post', verbose=self.service_context.args.verbose)
                    send_message(out_sock, r_msg, **self.service_context.send_recv_kwargs)
            else:
                raise ServiceError('unknown return type from the handler')

        except BlockMessage:
            pass
        except EventLoopEnd:
            send_message(out_sock, msg, **self.service_context.send_recv_kwargs)
            raise EventLoopEnd
        except ServiceError as ex:
            self.logger.error(ex, exc_info=True)


class ConcurrentService(type):
    _dct = {}

    def __new__(cls, name, bases, dct):
        _cls = super().__new__(cls, name, bases, dct)
        ConcurrentService._dct.update({name: {'cls': cls,
                                              'name': name,
                                              'bases': bases,
                                              'dct': dct}})
        return _cls

    def __call__(cls, *args, **kwargs):
        # switch to the new backend
        _cls = {
            'thread': threading.Thread,
            'process': multiprocessing.Process
        }[args[0].parallel_backend]

        # rebuild the class according to mro
        for c in cls.mro()[-2::-1]:
            arg_cls = ConcurrentService._dct[c.__name__]['cls']
            arg_name = ConcurrentService._dct[c.__name__]['name']
            arg_dct = ConcurrentService._dct[c.__name__]['dct']
            _cls = super().__new__(arg_cls, arg_name, (_cls,), arg_dct)

        return type.__call__(_cls, *args, **kwargs)


class BaseService(metaclass=ConcurrentService):
    handler = MessageHandler()
    default_host = '0.0.0.0'

    def _get_event(self):
        if isinstance(self, threading.Thread):
            return threading.Event()
        elif isinstance(self, multiprocessing.Process):
            return multiprocessing.Event()
        else:
            raise NotImplementedError

    def __init__(self, args):
        super().__init__()
        if 'py_path' in args and args.py_path:
            PathImporter.add_modules(*args.py_path)
        self.args = args
        self.logger = set_logger(self.__class__.__name__, args.verbose)
        self.is_ready = self._get_event()
        self.is_event_loop = self._get_event()
        self.is_model_changed = self._get_event()
        self.is_handler_done = self._get_event()
        self.last_dump_time = time.perf_counter()
        self._model = None
        self.use_event_loop = True
        self.ctrl_addr = 'tcp://%s:%d' % (self.default_host, self.args.port_ctrl)
        self.logger.info('control address: %s' % self.ctrl_addr)
        self.send_recv_kwargs = dict(
            check_version=self.args.check_version,
            timeout=self.args.timeout,
            squeeze_pb=self.args.squeeze_pb)
        self._override_handler()

    def _override_handler(self):
        # replace the function name by the function itself
        mh = MessageHandler()
        mh.routes = {k: getattr(self, v) for k, v in self.handler.routes.items()}
        mh.hooks = {k: [(getattr(self, vv[0]), vv[1]) for vv in v] for k, v in self.handler.hooks.items()}
        self.handler = mh

    def run(self):
        try:
            self._run()
        except Exception as ex:
            self.logger.error(ex, exc_info=True)

    def dump(self, respect_dump_interval: bool = True):
        if (not self.args.read_only
                and self.args.dump_interval > 0
                and self._model
                and self.is_model_changed.is_set()
                and ((respect_dump_interval
                      and (time.perf_counter() - self.last_dump_time) > self.args.dump_interval)
                     or not respect_dump_interval)):
            self.is_model_changed.clear()
            self.logger.info('dumping changes to the model, %3.0fs since last the dump'
                             % (time.perf_counter() - self.last_dump_time))
            self._model.dump()
            self.last_dump_time = time.perf_counter()
            self.logger.info('dumping finished! next dump will start in at least %3.0fs' % self.args.dump_interval)

    @handler.register_hook(hook_type='post')
    def _hook_warn_body_type_change(self, msg: 'gnes_pb2.Message', *args, **kwargs):
        new_type = msg.WhichOneof('body')
        if new_type != self._msg_old_type:
            self.logger.warning('message body type has changed from "%s" to "%s"' % (self._msg_old_type, new_type))

    @handler.register_hook(hook_type='post')
    def _hook_sort_response(self, msg: 'gnes_pb2.Message', *args, **kwargs):
        if 'sorted_response' in self.args and self.args.sorted_response and msg.response.search.topk_results:
            msg.response.search.topk_results.sort(key=lambda x: x.score.value,
                                                  reverse=msg.response.search.is_big_score_similar)

            msg.response.search.is_sorted = True
            self.logger.info('sorted %d results in %s order' %
                             (len(msg.response.search.topk_results),
                              'descending' if msg.response.search.is_big_score_similar else 'ascending'))

    @handler.register_hook(hook_type='pre')
    def _hook_add_route(self, msg: 'gnes_pb2.Message', *args, **kwargs):
        add_route(msg.envelope, self._model.__class__.__name__, self.args.identity)
        self._msg_old_type = msg.WhichOneof('body')
        self.logger.info('a message in type: %s with route: %s' % (self._msg_old_type, router2str(msg)))

    @handler.register_hook(hook_type='post')
    def _hook_update_route_timestamp(self, msg: 'gnes_pb2.Message', *args, **kwargs):
        msg.envelope.routes[-1].end_time.GetCurrentTime()
        if self.args.route_table:
            self.logger.info('route: %s' % router2str(msg))
            self.logger.info('route table: \n%s' % make_route_table(msg.envelope.routes))

    @zmqd.context()
    def _run(self, ctx):
        ctx.setsockopt(zmq.LINGER, 0)
        self.handler.service_context = self
        # print('!!!! t_id: %d service_context: %r' % (threading.get_ident(), self.handler.service_context))
        self.logger.info('bind sockets...')
        in_sock, _ = build_socket(ctx, self.args.host_in, self.args.port_in, self.args.socket_in,
                                  self.args.identity)
        out_sock, _ = build_socket(ctx, self.args.host_out, self.args.port_out, self.args.socket_out,
                                   self.args.identity)
        ctrl_sock, ctrl_addr = build_socket(ctx, self.default_host, self.args.port_ctrl, SocketType.PAIR_BIND)

        self.logger.info(
            'input %s:%s\t output %s:%s\t control over %s' % (
                self.args.host_in, colored(self.args.port_in, 'yellow'),
                self.args.host_out, colored(self.args.port_out, 'yellow'),
                colored(ctrl_addr, 'yellow')))

        poller = zmq.Poller()
        poller.register(in_sock, zmq.POLLIN)
        poller.register(ctrl_sock, zmq.POLLIN)

        try:
            self.post_init()
            self.is_ready.set()
            self.is_event_loop.set()
            self.logger.critical('ready and listening')
            while self.is_event_loop.is_set():
                socks = dict(poller.poll(1))
                if socks.get(in_sock) == zmq.POLLIN:
                    pull_sock = in_sock
                elif socks.get(ctrl_sock) == zmq.POLLIN:
                    pull_sock = ctrl_sock
                else:
                    # no message received, pass
                    continue

                if self.use_event_loop or pull_sock == ctrl_sock:
                    with TimeContext('handling message', self.logger):
                        self.is_handler_done.clear()

                        # receive message
                        msg = recv_message(pull_sock, **self.send_recv_kwargs)

                        # choose output sock
                        if msg.request and msg.request.WhichOneof('body') and \
                                isinstance(getattr(msg.request, msg.request.WhichOneof('body')),
                                           gnes_pb2.Request.ControlRequest):
                            o_sock = ctrl_sock
                        else:
                            o_sock = out_sock

                        # call pre-hooks
                        self.handler.call_hooks(msg, hook_type='pre')
                        # call main handler and send result back
                        self.handler.call_routes_send_back(msg, o_sock)

                        self.is_handler_done.set()
                else:
                    self.logger.warning(
                        'received a new message but since "use_event_loop=False" I will not handle it. '
                        'I will just block the thread until "is_handler_done" is set!')
                    # wait until some one else call is_handler_done.set()
                    self.is_handler_done.wait()
                    # clear the handler status
                    self.is_handler_done.clear()

                # block the event loop if a dump is needed
                self.dump()
        except EventLoopEnd:
            self.logger.info('break from the event loop')
        except ComponentNotLoad:
            self.logger.error('component can not be correctly loaded, terminated')
        except Exception as ex:
            self.logger.error('unknown exception: %s' % str(ex), exc_info=True)
        finally:
            self.is_ready.set()
            self.is_event_loop.clear()
            in_sock.close()
            out_sock.close()
            ctrl_sock.close()
            # do not check dump_interval constraint as the last dump before close
            self.dump(respect_dump_interval=False)
        self.logger.critical('terminated')

    def post_init(self):
        pass

    def load_model(self, base_class: Type[TrainableBase], yaml_path=None) -> T:
        try:
            return base_class.load_yaml(self.args.yaml_path if not yaml_path else yaml_path)
        except FileNotFoundError:
            raise ComponentNotLoad

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
            msg.response.control.status = gnes_pb2.Response.READY
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
        r = None
        try:
            r = recv_message(sock, timeout)
        except TimeoutError:
            pass
        finally:
            sock.close()
        return r


class ServiceManager:
    def __init__(self, service_cls, args):
        self.logger = set_logger(self.__class__.__name__, args.verbose)

        self.services = []  # type: List['BaseService']
        if args.num_parallel > 1:
            from .router import RouterService
            _head_router = copy.deepcopy(args)
            _head_router.yaml_path = resolve_yaml_path('BaseRouter')
            _head_router.port_ctrl = self._get_random_port()
            port_out = self._get_random_port()
            _head_router.port_out = port_out

            _tail_router = copy.deepcopy(args)
            _tail_router.yaml_path = resolve_yaml_path('BaseRouter')
            port_in = self._get_random_port()
            _tail_router.port_in = port_in
            _tail_router.port_ctrl = self._get_random_port()

            _tail_router.socket_in = SocketType.PULL_BIND

            if args.parallel_type.is_push:
                _head_router.socket_out = SocketType.PUSH_BIND
            else:
                _head_router.socket_out = SocketType.PUB_BIND
                _head_router.yaml_path = resolve_yaml_path(
                    '!PublishRouter {parameters: {num_part: %d}}' % args.num_parallel)

            if args.parallel_type.is_block:
                _tail_router.yaml_path = resolve_yaml_path('BaseReduceRouter')
                _tail_router.num_part = args.num_parallel

            self.services.append(RouterService(_head_router))
            self.services.append(RouterService(_tail_router))

            for _ in range(args.num_parallel):
                _args = copy.deepcopy(args)
                _args.port_in = port_out
                _args.port_out = port_in
                _args.port_ctrl = self._get_random_port()
                _args.socket_out = SocketType.PUSH_CONNECT
                if args.parallel_type.is_push:
                    _args.socket_in = SocketType.PULL_CONNECT
                else:
                    _args.socket_in = SocketType.SUB_CONNECT
                self.services.append(service_cls(_args))
            self.logger.info('num_parallel=%d, add a router with port_in=%d and a router with port_out=%d' % (
                args.num_parallel, _head_router.port_in, _tail_router.port_out))
        else:
            self.services.append(service_cls(args))

    @staticmethod
    def _get_random_port(min_port: int = 49152, max_port: int = 65536) -> int:
        return random.randrange(min_port, max_port)

    def __enter__(self):
        self.stack = ExitStack()
        for s in self.services:
            self.stack.enter_context(s)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stack.close()

    def join(self):
        for s in self.services:
            s.join()
