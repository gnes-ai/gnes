from collections import defaultdict
from typing import Dict

import zmq

from .base import BaseService as BS, MessageHandler
from ..helper import batch_iterator
from ..messaging import *
from zmq.utils import jsonapi


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
                if self.args.num_part and self.args.num_part >= 2:
                    tmp = {}
                    for _msg in self.pending_result[msg.unique_id]:
                        if _msg.part_id in tmp:
                            tmp[_msg.part_id].append(jsonapi.loads(_msg.msg_content))
                        else:
                            tmp[_msg.part_id] = [jsonapi.loads(_msg.msg_content)]
                    res = None
                    for _id in sorted(tmp.keys()):
                        # m (shards) * n (samples) * k (top k) -> n * m * k
                        msg_content = list(zip(*tmp[_id]))
                        top_k = len(msg_content[0][0])
                        msg_content = [sorted([i for j in v for i in j],
                                              key=lambda x: -x[1])[:top_k]
                                       for v in msg_content]
                        if res:
                            res += msg_content
                        else:
                            res = msg_content
                else:
                    tmp = sorted(self.pending_result[msg.unique_id], key=lambda v: v.part_id)
                    res = [d for v in tmp for d in v.msg_content]
                send_message(out,
                             msg.copy_mod(msg_content=res,
                                          part_id=1,
                                          num_part=1), self.args.timeout)
            else:
                send_message(out, msg, self.args.timeout)
            self.pending_result.pop(msg.unique_id)
