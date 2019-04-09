import uuid

import zmq

from ..base import TrainableBase
from ..messaging import send_message, Message


class BaseClient(TrainableBase):
    def __init__(self, host_in: str = 'localhost',
                 host_out: str = 'localhost',
                 port_in: int = 5555, port_out: int = 5556,
                 identity: str = None, timeout: int = -1,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.identity = identity or str(uuid.uuid4())
        self.timeout = timeout
        self._context = zmq.Context()

        self._sender = self._context.socket(zmq.PUSH)
        self._sender.setsockopt(zmq.LINGER, 0)
        self._sender.connect('tcp://%s:%d' % (host_in, port_in))

        self._receiver = self._context.socket(zmq.SUB)
        self._receiver.setsockopt(zmq.LINGER, 0)
        self._receiver.setsockopt(zmq.SUBSCRIBE, self.identity.encode('ascii'))
        self._receiver.connect('tcp://%s:%d' % (host_out, port_out))

    def send(self, texts):
        req_id = str(uuid.uuid4())
        send_message(self._sender, Message(client_id=self.identity,
                                           req_id=req_id,
                                           msg_content=texts,
                                           route='client'), timeout=self.timeout)

    def send_receive(self, texts):
        self.send(texts)
        response = self._receiver.recv_multipart()
        return Message.from_bytes(*response)

    def close(self):
        self._sender.close()
        self._receiver.close()
        self._context.term()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
