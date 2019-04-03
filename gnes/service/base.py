import threading
from enum import Enum

import zmq
import zmq.decorators as zmqd
from termcolor import colored

from ..helper import set_logger
from ..messaging import *


class ServiceMode(Enum):
    TRAIN = 0
    ADD = 1
    QUERY = 2

    def __str__(self):
        return self.name

    @staticmethod
    def from_string(s):
        try:
            return ServiceMode[s]
        except KeyError:
            raise ValueError()


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

    def __init__(self, args):
        super().__init__()
        self.args = args
        self.logger = set_logger(self.__class__.__name__, self.args.verbose)
        self.is_ready = threading.Event()

    def run(self):
        self._run()

    def message_handler(self, msg: Message):
        try:
            fn = self.handler.serve(msg)
            if fn:
                msg.route += ' -> '.join([msg.route, self.__class__.__name__])
                self.logger.info('handling a message of type: %s with route: %s' % (msg.msg_type, msg.route))
                fn(self, msg, self.ctrl_sock if msg.is_control_message else self.out_sock)
        except ServiceError as e:
            self.logger.error(e)

    @zmqd.context()
    @zmqd.socket(zmq.PULL)
    @zmqd.socket(zmq.PUSH)
    @zmqd.socket(zmq.PAIR)
    def _run(self, _, in_sock: 'zmq.Socket', out_sock: 'zmq.Socket', ctrl_sock: 'zmq.Socket'):
        _.setsockopt(zmq.LINGER, 0)
        self.logger.info('bind sockets...')
        in_sock.bind('tcp://%s:%d' % (self.args.host, self.args.port_in))
        out_sock.bind('tcp://%s:%d' % (self.args.host, self.args.port_out))
        ctrl_sock.bind('tcp://%s:%d' % (self.args.host, self.args.port_ctrl))
        self.in_sock, self.out_sock, self.ctrl_sock = in_sock, out_sock, ctrl_sock

        self.logger.info(
            'host: %s listen on %s\t output to %s\t control over %s' % (
                colored(self.args.host, 'yellow'),
                colored(self.args.port_in, 'yellow'),
                colored(self.args.port_out, 'yellow'),
                colored(self.args.port_ctrl, 'yellow')))

        poller = zmq.Poller()
        poller.register(in_sock, zmq.POLLIN)
        poller.register(ctrl_sock, zmq.POLLIN)

        try:
            self._post_init()
            self.is_ready.set()
            self.logger.info('ready and listening')
            while True:
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
        except StopIteration:
            self.logger.info('terminated')
        except ComponentNotLoad:
            self.logger.error('component can not be correctly loaded, terminated')
        finally:
            self.is_ready.set()

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
        raise StopIteration

    def close(self):
        send_terminate_message(self.args.host, self.args.port_ctrl)

    @property
    def status(self):
        return send_ctrl_message(self.args.host, self.args.port_ctrl, Message(msg_type=Message.typ_status))

    def __enter__(self):
        self.start()
        self.is_ready.wait()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
