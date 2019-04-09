import threading
import time
from enum import Enum

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


class SocketType(BetterEnum):
    PULL_BIND = 0
    PULL_CONNECT = 1
    PUSH_BIND = 2
    PUSH_CONNECT = 3
    SUB_BIND = 4
    SUB_CONNECT = 5
    PUB_BIND = 6
    PUB_CONNECT = 7

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


class MessageHandler:
    def __init__(self, mh: 'MessageHandler' = None):
        self.routes = {k: v for k, v in mh.routes.items()} if mh else {}
        self.logger = set_logger(self.__class__.__name__)

    def register(self, msg_type: str):
        def decorator(f):
            self.routes[msg_type] = f
            return f

        return decorator

    def serve(self, msg: Message):
        if not isinstance(msg, Message):
            raise ServiceError('dont know how to handle message: %s' % msg)
        fn = self.routes.get(msg.msg_type, None)
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
        self._model = None

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
        except ServiceError as e:
            self.logger.error(e)

    @zmqd.context()
    @zmqd.socket(zmq.PAIR)
    def _run(self, ctx, ctrl_sock: 'zmq.Socket'):
        ctx.setsockopt(zmq.LINGER, 0)
        self.logger.info('bind sockets...')
        ctrl_sock.bind('tcp://%s:%d' % (self.default_host, self.args.port_ctrl))
        in_sock = {
            SocketType.PULL_BIND: lambda: ctx.socket(zmq.PULL),
            SocketType.PULL_CONNECT: lambda: ctx.socket(zmq.PULL),
            SocketType.SUB_BIND: lambda: ctx.socket(zmq.SUB),
            SocketType.SUB_CONNECT: lambda: ctx.socket(zmq.SUB)
        }[self.args.socket_in]()

        out_sock = {
            SocketType.PUB_BIND: lambda: ctx.socket(zmq.PUB),
            SocketType.PUB_CONNECT: lambda: ctx.socket(zmq.PUB),
            SocketType.PUSH_BIND: lambda: ctx.socket(zmq.PUSH),
            SocketType.PUSH_CONNECT: lambda: ctx.socket(zmq.PUSH)
        }[self.args.socket_out]()

        if self.args.socket_in.is_bind:
            in_sock.bind('tcp://%s:%d' % (self.args.host_in, self.args.port_in))
        else:
            in_sock.connect('tcp://%s:%d' % (self.args.host_in, self.args.port_in))

        if self.args.socket_out.is_bind:
            out_sock.bind('tcp://%s:%d' % (self.args.host_out, self.args.port_out))
        else:
            out_sock.connect('tcp://%s:%d' % (self.args.host_out, self.args.port_out))

        self.in_sock, self.out_sock, self.ctrl_sock = in_sock, out_sock, ctrl_sock

        self.logger.info(
            'input %s:%s\t output %s:%s\t control over %s:%s' % (
                self.args.host_in, colored(self.args.port_in, 'yellow'),
                self.args.host_out, colored(self.args.port_out, 'yellow'),
                self.default_host, colored(self.args.port_ctrl, 'yellow')))

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
                self.message_handler(msg)
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
        send_message(out, msg)
        self.is_event_loop.clear()
        raise StopIteration

    def close(self):
        if self._model:
            self.dump()
            self._model.close()
        if self.is_event_loop.is_set():
            send_terminate_message(self.default_host, self.args.port_ctrl)

    @property
    def status(self):
        return send_ctrl_message(self.default_host, self.args.port_ctrl, Message(msg_type=Message.typ_status))

    def __enter__(self):
        self.start()
        self.is_ready.wait()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
