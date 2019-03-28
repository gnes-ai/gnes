import threading
from typing import Union, List, Optional, Any

import numpy as np
import zmq
import zmq.decorators as zmqd
from termcolor import colored
from zmq.utils import jsonapi

from ..helper import set_logger


class Message:
    prefix_ctrl = 'CTRL_'
    typ_terminate = prefix_ctrl + 'TERMINATE'
    typ_status = prefix_ctrl + 'STATUS'
    typ_default = 'DEFAULT'
    typ_train = 'TRAIN'

    def __init__(self,
                 client_id: Union[bytes, str] = b'',
                 req_id: Union[bytes, str] = b'',
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
        self.client_id = client_id
        self.req_id = req_id
        self.msg_type = msg_type
        self.content_type = content_type
        self.msg_content = msg_content
        self.route = route

    def to_bytes(self) -> List[bytes]:
        return [self._client_id, self._req_id, self._msg_type, self._msg_content, self._content_type, self._route]

    @staticmethod
    def from_bytes(client_id, req_id, msg_type, msg_content, content_type, route):
        x = Message()
        x._client_id = client_id
        x._req_id = req_id
        x._msg_type = msg_type
        x._msg_content = msg_content
        x._content_type = content_type
        x._route = route
        return x

    def copy_mod(self, **kwargs) -> 'Message':
        y = Message()
        y._client_id = self._client_id
        y._req_id = self._req_id
        y._msg_type = self._msg_type
        y._msg_content = self._msg_content
        y._route = self._route
        y._content_type = self._content_type
        for k, v in kwargs.items():
            setattr(y, k, v)
        return y

    def __repr__(self):
        return 'client_id: %s, req_id: %s, msg_type: %s, msg_content: %s, route: %s' % \
               (self.client_id, self.req_id, self.msg_type, self.msg_content, self.route)

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
        ct = self.content_type
        if 'dtype' in ct and 'shape' in ct:
            return np.frombuffer(memoryview(self._msg_content), dtype=str(ct['dtype'])).reshape(ct['shape'])
        return jsonapi.loads(self._msg_content)

    @msg_content.setter
    def msg_content(self, value: Any):
        if isinstance(value, np.ndarray):
            array_info = dict(dtype=str(value.dtype), shape=value.shape)
            self.content_type = array_info
            self._msg_content = value
        else:
            if isinstance(value, bytes):
                value = value.decode()
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


def send_message(sock: 'zmq.Socket', msg: 'Message', timeout: int = -1) -> None:
    try:
        if timeout > 0:
            sock.setsockopt(zmq.SNDTIMEO, timeout)
        else:
            sock.setsockopt(zmq.SNDTIMEO, -1)

        sock.send_multipart(msg.to_bytes())
    except zmq.error.Again:
        raise TimeoutError(
            'no response from sock %s after timeout=%dms, please check the following:'
            'is the server still online? is the network broken? are "port" correct? ' % (
                sock, timeout))
    finally:
        sock.setsockopt(zmq.SNDTIMEO, -1)


def recv_message(sock: 'zmq.Socket', timeout: int = -1) -> Optional['Message']:
    response = []
    try:
        if timeout > 0:
            sock.setsockopt(zmq.RCVTIMEO, timeout)
        else:
            sock.setsockopt(zmq.RCVTIMEO, -1)
        response = sock.recv_multipart()
        return Message.from_bytes(*response)
    except ValueError:
        raise ValueError('received a wrongly-formatted request (expected 4 frames, got %d)' % len(response))
    except zmq.error.Again:
        raise TimeoutError(
            'no response from sock %s after timeout=%dms, please check the following:'
            'is the server still online? is the network broken? are "port" correct? ' % (
                sock, timeout))
    finally:
        sock.setsockopt(zmq.RCVTIMEO, -1)


def send_ctrl_message(address: str, port: int, msg: Message, timeout: int = 2000):
    # control message is short, set a timeout and ask for quick response
    with zmq.Context() as ctx:
        ctx.setsockopt(zmq.LINGER, 0)
        with ctx.socket(zmq.PAIR) as ctrl_sock:
            ctrl_sock.connect('tcp://%s:%d' % (address, port))
            send_message(ctrl_sock, msg, timeout)
            return recv_message(ctrl_sock, timeout)


def send_terminate_message(*args, **kwargs):
    return send_ctrl_message(msg=Message(msg_type=Message.typ_terminate), *args, **kwargs)


class MessageHandler:
    def __init__(self):
        self.routes = {}
        self.logger = set_logger(self.__class__.__name__)

    def register(self, msg_type: str):
        def decorator(f):
            self.routes[msg_type] = f
            return f

        return decorator

    def serve(self, msg: Message):
        if not isinstance(msg, Message):
            self.logger.error('dont know how to handle message: %s' % msg)
        fn = self.routes.get(msg.msg_type, None)
        if fn is None:
            self.logger.error('dont know how to handle message with type: %s' % msg.msg_type)
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
        fn = self.handler.serve(msg)
        if fn:
            msg.route += ' -> '.join([msg.route, self.__class__.__name__])
            fn(self, msg, self.ctrl_sock if msg.is_control_message else self.out_sock)

    @zmqd.context()
    @zmqd.socket(zmq.PULL)
    @zmqd.socket(zmq.PUSH)
    @zmqd.socket(zmq.PAIR)
    def _run(self, _, in_sock: 'zmq.Socket', out_sock: 'zmq.Socket', ctrl_sock: 'zmq.Socket'):
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

        self._post_init()
        self.is_ready.set()

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
                msg = recv_message(pull_sock)
                self.message_handler(msg)
        except StopIteration:
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
