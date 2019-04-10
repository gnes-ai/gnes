import uuid
from typing import List, Optional

import zmq

from .base import BaseService as BS, MessageHandler
from ..messaging import *


class ClientService(BS):
    handler = MessageHandler(BS.handler)

    def _post_init(self):
        self.in_sock.setsockopt(zmq.SUBSCRIBE, self.args.identity.encode('ascii'))
        self.result = []

    @handler.register(Message.typ_default)
    def _handler_default(self, msg: 'Message', out: 'zmq.Socket'):
        self.result.append(msg)

    def query(self, texts: List[str]) -> Optional['Message']:
        req_id = str(uuid.uuid4())
        send_message(self.out_sock, Message(client_id=self.args.identity,
                                            req_id=req_id,
                                            msg_content=texts,
                                            route=self.__class__.__name__), timeout=self.args.timeout)
        if self.args.wait_reply:
            self.is_handler_done.wait(self.args.timeout)
            return self.result.pop()
