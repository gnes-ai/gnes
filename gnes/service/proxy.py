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
        if msg.num_part > 1:
            self.pending_result[msg.unique_id].append(msg)
            if msg.num_part == len(self.pending_result[msg.unique_id]):
                tmp = sorted(self.pending_result[msg.unique_id], key=lambda v: v.part_id)
                send_message(out,
                             msg.copy_mod(msg_content=[d for v in tmp for d in v.msg_content],
                                          part_id=1,
                                          num_part=1), self.args.timeout)
                self.pending_result.pop(msg.unique_id)
        else:
            send_message(out, msg, self.args.timeout)
