from typing import List

from ..base import BaseRequestGenerator
from ... import gnes_pb2
from ....helper import batch_iterator


class TextRequestGenerator(BaseRequestGenerator):
    def index(self, docs: List[str], batch_size: int = 0, *args, **kwargs):
        p = [r for r in docs if r.strip()]
        for pi in batch_iterator(p, batch_size):
            req = gnes_pb2.Request()
            for raw_text in pi:
                d = req.index.docs.add()
                d.raw_text = raw_text
            yield req

    def train(self, docs: List[str], batch_size: int = 0, *args, **kwargs):
        p = [r for r in docs if r.strip()]
        for pi in batch_iterator(p, batch_size):
            req = gnes_pb2.Request()
            for raw_text in pi:
                d = req.train.docs.add()
                d.raw_text = raw_text
            yield req
        req = gnes_pb2.Request()
        req.flush = True
        yield req

    def query(self, query: str, top_k: int, *args, **kwargs):
        if top_k <= 0:
            raise ValueError('"top_k: %d" is not a valid number' % top_k)

        req = gnes_pb2.Request()
        req.search.query.raw_text = query
        req.search.top_k = top_k
        yield req
