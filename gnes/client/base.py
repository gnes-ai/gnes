import uuid

import zmq

from ..base import TrainableBase
from ..messaging import send_message, Message


class BaseClient(TrainableBase):
    def __init__(self, host_in: str,
                 host_out: str,
                 port_in: int, port_out: int,
                 timeout: int, identity: str = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.identity = identity or str(uuid.uuid4())
        self.timeout = timeout
        self._context = zmq.Context()

        self._sender = self._context.socket(zmq.PUSH)
        self._sender.connect('tcp://%s:%d' % (host_in, port_in))

        self._receiver = self._context.socket(zmq.SUB)
        self._receiver.setsockopt(zmq.SUBSCRIBE, self.identity.encode('ascii'))
        self._receiver.connect('tcp://%s:%d' % (host_out, port_out))

    def send(self, texts):
        req_id = str(uuid.uuid4())
        send_message(self._sender, Message(client_id=self.identity,
                                           req_id=req_id,
                                           msg_content=texts,
                                           route=self.__class__.__name__), timeout=self.timeout)

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
