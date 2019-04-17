import threading
import time
from enum import Enum
from typing import Tuple

import zmq
import zmq.decorators as zmqd
from termcolor import colored

from ..helper import set_logger
from ..messaging import *


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


class ServiceMode(BetterEnum):
    TRAIN = 0
    ADD = 1
    QUERY = 2


class ComponentNotLoad(Exception):
    pass


class ServiceError(Exception):
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

    return sock, sock.getsockopt_string(zmq.LAST_ENDPOINT)


class MessageHandler:
    def __init__(self, mh: 'MessageHandler' = None):
        self.routes = {k: v for k, v in mh.routes.items()} if mh else {}
        self.logger = set_logger(self.__class__.__name__)
        self.any_msg_route = None

    def register(self, msg_type: str):
        def decorator(f):
            self.routes[msg_type] = f
            return f

        return decorator

    def serve(self, msg: Message):
        if not isinstance(msg, Message):
            raise ServiceError('dont know how to handle message: %s' % msg)

        _any_msg_fn = self.routes.get(self.any_msg_route)
        fn = self.routes.get(msg.msg_type, _any_msg_fn)
        if fn is None:
            raise ServiceError('dont know how to handle message with type: %s' % msg.msg_type)
        else:
            return fn


class BaseService(threading.Thread):
    handler = MessageHandler()
    default_host = '0.0.0.0'

    def __init__(self, args):
        super().__init__()
        self.args = args
        self.logger = set_logger(self.__class__.__name__, self.args.verbose)
        self.is_ready = threading.Event()
        self.is_event_loop = threading.Event()
        self.is_model_changed = threading.Event()
        self.is_handler_done = threading.Event()
        self._model = None
        self.identity = args.identity if 'identity' in args else None

        # forward message that does not match with any registed routes
        handler.any_msg_route = self.args.any_msg_route if 'any_msg_route' in args else None

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

    def dump(self):
        if not self.args.read_only:
            if self._model:
                self.logger.info('dumping changes to the model...')
                self._model.dump(self.args.dump_path)
                self.logger.info('dumping finished!')
        else:
            self.logger.warning('dumping is not allowed as "read_only" is set to true.')

    def message_handler(self, msg: Message):
        try:
            fn = self.handler.serve(msg)
            if fn:
                msg.route = ' -> '.join([msg.route, self.__class__.__name__])
                self.logger.info('handling a message of type: %s with route: %s' % (msg.msg_type, msg.route))
                fn(self, msg, self.ctrl_sock if msg.is_control_message else self.out_sock)
                self.logger.info('handler is done')
        except ServiceError as e:
            self.logger.error(e)

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
            self._post_init()
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
                msg = recv_message(pull_sock)
                self.is_handler_done.clear()
                self.message_handler(msg)
                self.is_handler_done.set()
                if self.args.dump_interval == 0:
                    self.dump()
        except StopIteration:
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

    def _post_init(self):
        pass

    @handler.register(Message.typ_default)
    def _handler_default(self, msg: Message, out: 'zmq.Socket'):
        pass

    @handler.register(Message.typ_status)
    def _handler_status(self, msg: Message, out: 'zmq.Socket'):
        pass

    @handler.register(Message.typ_terminate)
    def _handler_terminate(self, msg: Message, out: 'zmq.Socket'):
        send_message(out, msg, self.args.timeout)
        self.is_event_loop.clear()
        raise StopIteration

    def close(self):
        if self._model:
            self.dump()
            self._model.close()
        if self.is_event_loop.is_set():
            send_terminate_message(self.ctrl_addr, timeout=self.args.timeout)

    @property
    def status(self):
        return send_ctrl_message(self.ctrl_addr, Message(msg_type=Message.typ_status), self.args.time_out)

    def __enter__(self):
        self.start()
        self.is_ready.wait()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def send_ctrl_message(address: str, msg: Message, timeout: int):
    # control message is short, set a timeout and ask for quick response
    with zmq.Context() as ctx:
        ctx.setsockopt(zmq.LINGER, 0)
        sock, _ = build_socket(ctx, address, None, SocketType.PAIR_CONNECT)
        send_message(sock, msg, timeout)
        r = recv_message(sock, timeout)
        sock.close()
        return r


def send_terminate_message(*args, **kwargs):
    return send_ctrl_message(msg=Message(msg_type=Message.typ_terminate), *args, **kwargs)
