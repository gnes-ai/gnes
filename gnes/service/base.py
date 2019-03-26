import threading
from typing import Dict, Callable, Union

import zmq
import zmq.decorators as zmqd
from termcolor import colored

from ..helper import set_logger


class Message:
    prefix_ctrl = 'CTRL_'
    typ_terminate = prefix_ctrl + 'TERMINATE'
    typ_ready = prefix_ctrl + 'READY'
    typ_status = prefix_ctrl + 'STATUS'
    typ_default = 'DEFAULT'

    def __init__(self, client_id: Union[bytes, str] = b'',
                 req_id: Union[bytes, str] = b'',
                 msg_type: Union[bytes, str] = typ_default,
                 msg_content: Union[bytes, str] = b'',
                 route: Union[bytes, str] = b''):
        self._client_id = b''
        self._req_id = b''
        self._msg_type = b''
        self._msg_content = b''
        self._route = b''
        self.client_id = client_id
        self.req_id = req_id
        self.msg_type = msg_type
        self.msg_content = msg_content
        self.route = route

    @property
    def is_control_message(self) -> bool:
        return self.msg_type.startswith(Message.prefix_ctrl)

    @property
    def client_id(self):
        return self._client_id.decode()

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
        return self._msg_content.decode()

    @msg_content.setter
    def msg_content(self, value: Union[str, bytes]):
        if not isinstance(value, bytes):
            value = value.encode()
        self._msg_content = value

    @property
    def route(self):
        return self._route.decode()

    @route.setter
    def route(self, value: Union[str, bytes]):
        if not isinstance(value, bytes):
            value = value.encode()
        self._route = value


def send_message(sock: 'zmq.Socket', msg: 'Message') -> None:
    sock.send_multipart([msg.client_id, msg.req_id, msg.msg_type, msg.msg_content, msg.route])


def send_ctrl_message(address: str, port: int, msg: Message, timeout: int = 5000) -> None:
    with zmq.Context() as ctx:
        ctx.setsockopt(zmq.LINGER, timeout)
        with ctx.socket(zmq.PAIR) as ctrl_sock:
            try:
                ctrl_sock.connect('tcp://%s:%d' % (address, port))
                send_message(ctrl_sock, msg)
            except zmq.error.Again:
                raise TimeoutError(
                    'no response from %s:%d (with "timeout"=%d ms), please check the following:'
                    'is the server still online? is the network broken? are "port" correct? ' % (
                        address, port, timeout))


def send_terminate_message(*args, **kwargs) -> None:
    send_ctrl_message(msg=Message(msg_type=Message.typ_terminate), *args, **kwargs)


class BaseService(threading.Thread):
    def __init__(self, args):
        super().__init__()
        self.verbose = 'verbose' in args and args['verbose']
        self.logger = set_logger(self.__class__.__name__, self.verbose)
        self.args = args
        self._handler = {}  # type: Dict[str, Callable]
        self.register_handler(Message.typ_terminate, self.handler_terminate)
        self.register_handler(Message.typ_ready, self.handler_ready)
        self.register_handler(Message.typ_default, self.handler_default)
        self.register_handler(Message.typ_status, self.handler_status)

    def run(self):
        self._run()

    def message_handler(self, msg: Message):
        fn = self._handler.get(msg.msg_type, None)
        if fn is None:
            self.logger.error('dont know how to handle message with type: %s' % msg.msg_type)
        else:
            msg.route += ' : ' + self.__class__.__name__
            fn(msg, self.ctrl_sock if msg.is_control_message else self.out_sock)

    def register_handler(self, msg_type: str, handler: Callable):
        if msg_type in self._handler:
            self.logger.warning('handler of the message type: %s is already registered, will override' % msg_type)
        self._handler[msg_type] = handler

    @zmqd.context()
    @zmqd.socket(zmq.PULL)
    @zmqd.socket(zmq.PUSH)
    @zmqd.socket(zmq.PAIR)
    def _run(self, _, in_sock: 'zmq.Socket', out_sock: 'zmq.Socket', ctrl_sock: 'zmq.Socket'):
        in_sock.bind('tcp://%s:%d' % (self.args.address_in, self.args.port_in))
        out_sock.bind('tcp://%s:%d' % (self.args.address_out, self.args.port_out))
        ctrl_sock.bind('tcp://%s:%d' % (self.args.address_ctrl, self.args.port_ctrl))
        self.in_sock, self.out_sock, self.ctrl_sock = in_sock, out_sock, ctrl_sock

        self.logger.info(
            'listen on %s\t output to %s\t control over %s' % (
                colored('%s:%d' % (self.args.address_in, self.args.port_in), 'yellow'),
                colored('%s:%d' % (self.args.address_out, self.args.port_out), 'yellow'),
                colored('%s:%d' % (self.args.address_ctrl, self.args.port_ctrl), 'yellow')
            ))

        poller = zmq.Poller()
        poller.register(in_sock, zmq.POLLIN)
        poller.register(ctrl_sock, zmq.POLLIN)

        try:
            while True:
                pull_sock = None
                socks = dict(poller.poll())
                if socks.get(in_sock) == zmq.POLLIN:
                    pull_sock = in_sock
                elif socks.get(ctrl_sock) == zmq.POLLIN:
                    pull_sock = ctrl_sock
                else:
                    self.logger.error('received message from unknown socket: %s' % socks)

                try:
                    request = pull_sock.recv_multipart()
                    msg = Message(*request)
                except ValueError:
                    self.logger.error('received a wrongly-formatted request (expected 4 frames, got %d)' % len(request))
                    self.logger.error('\n'.join('field %d: %s' % (idx, k) for idx, k in enumerate(request)),
                                      exc_info=True)
                else:
                    self.message_handler(msg)
        except StopIteration:
            self.logger.info('terminated')

    def handler_default(self, msg: Message, out: 'zmq.Socket'):
        pass

    def handler_status(self, msg: Message, out: 'zmq.Socket'):
        pass

    def handler_terminate(self, msg: Message, out: 'zmq.Socket'):
        raise StopIteration

    def handler_ready(self, msg: Message, out: 'zmq.Socket'):
        pass

    def close(self):
        send_terminate_message(self.args.address_ctrl, self.args.port_ctrl)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
