import uuid
from typing import List, Optional

import zmq

from .base import BaseService as BS, MessageHandler
from ..messaging import *
from zmq.utils import jsonapi


class ClientService(BS):
    handler = MessageHandler(BS.handler)

    def _post_init(self):
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
            res = self.result.pop()
            tmp = {}
            for part_id, content in res:
                content = jsonapi.loads(content)
                if part_id in tmp:
                    tmp[part_id].append(content)
                else:
                    tmp[part_id] = content
            merged = None
            for k in sorted(tmp.keys()):
                _t = list(zip(*tmp[k]))
                _t = [sorted([i for j in v for i in j],
                             key=lambda x: -x[1])[:len(_t[0][0])]
                      for v in _t]
                merged = merged + _t if merged else _t
            return merged
