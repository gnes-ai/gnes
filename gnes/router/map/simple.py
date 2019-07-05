from typing import Generator

from ..base import BaseMapRouter
from ...helper import batch_iterator
from ...proto import gnes_pb2


class PublishRouter(BaseMapRouter):

    def __init__(self, num_part: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_part = num_part

    def apply(self, msg: 'gnes_pb2.Message', *args, **kwargs) -> Generator:
        msg.envelope.num_part = self.num_part
        yield msg


class DocBatchRouter(BaseMapRouter):
    def __init__(self, batch_size: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch_size = batch_size

    def apply(self, msg: 'gnes_pb2.Message', *args, **kwargs) -> Generator:
        if self.batch_size and self.batch_size > 0:
            batches = [b for b in batch_iterator(msg.request.index.docs, self.batch_size)]
            num_part = len(batches)
            for p_idx, b in enumerate(batches, start=1):
                _msg = gnes_pb2.Message()
                _msg.CopyFrom(msg)
                _msg.request.index.ClearField('docs')
                _msg.request.index.docs.extend(b)
                _msg.envelope.part_id = p_idx
                _msg.envelope.num_part = num_part
                yield _msg
