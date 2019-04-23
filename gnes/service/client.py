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
            if self.args.merge_res:
                tmp = {}
                for part_id, content in jsonapi.loads(res.msg_content):
                    if part_id in tmp:
                        tmp[part_id].append(content)
                    else:
                        tmp[part_id] = [content]
                merged = None
                print(tmp)
                for k in sorted(tmp.keys()):
                    _t = list(zip(*tmp[k]))
                    _top_k = _t[0][0]
                    _t = [sorted([i for j in v for i in j],
                                 key=lambda x: -x[1])[:len(_top_k)]
                          for v in _t]
                    merged = merged + _t if merged else _t
                return merged
            else:
                return res
