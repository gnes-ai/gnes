from collections import defaultdict
from typing import Dict

import zmq

from .base import BaseService as BS, MessageHandler
from ..helper import batch_iterator
from ..messaging import *


class ProxyService(BS):
    handler = MessageHandler(BS.handler)

    @handler.register(Message.typ_default)
    def _handler_default(self, msg: 'Message', out: 'zmq.Socket'):
        send_message(out, msg, self.args.timeout)


class MapProxyService(ProxyService):
    handler = MessageHandler(BS.handler)

    @handler.register(Message.typ_default)
    def _handler_default(self, msg: 'Message', out: 'zmq.Socket'):
        if not self.args.batch_size or self.args.batch_size <= 0:
            send_message(out, msg, self.args.timeout)
        else:
            batches = [b for b in batch_iterator(msg.msg_content, self.args.batch_size)]
            num_part = len(batches)
            for p_idx, b in enumerate(batches, start=1):
                send_message(out, msg.copy_mod(msg_content=b,
                                               part_id=p_idx,
                                               num_part=num_part), self.args.timeout)


class ReduceProxyService(ProxyService):
    handler = MessageHandler(BS.handler)

    def _post_init(self):
        self.pending_result = defaultdict(list)  # type: Dict[str, list]

    @handler.register(Message.typ_default)
    def _handler_default(self, msg: 'Message', out: 'zmq.Socket'):
        self.pending_result[msg.unique_id].append(msg)
        len_result = len(self.pending_result[msg.unique_id])
        if (not self.args.num_part and len_result == msg.num_part) or (
                self.args.num_part and len_result == self.args.num_part*msg.num_part):
            if len_result > 1:
                tmp = sorted(self.pending_result[msg.unique_id], key=lambda v: v.part_id)
                res = [(v.part_id, v.msg_content) for v in tmp]
                send_message(out,
                             msg.copy_mod(msg_content=res,
                                          part_id=1,
                                          num_part=1), self.args.timeout)
            else:
                send_message(out, msg, self.args.timeout)
            self.pending_result.pop(msg.unique_id)
