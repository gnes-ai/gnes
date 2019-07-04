from typing import List, TypeVar

from ..base import BaseRequestGenerator
from ... import gnes_pb2, image2blob
from ....helper import batch_iterator

T = TypeVar('T', bound='PIL.Image')


class ImageRequestGenerator(BaseRequestGenerator):
    def index(self, imgs: List[T], batch_size: int = 0, *args, **kwargs):
        p = [image2blob(j) for j in imgs]
        for pi in batch_iterator(p, batch_size):
            req = gnes_pb2.Request()
            for raw_img in pi:
                d = req.index.docs.add()
                d.raw_image.CopyFrom(raw_img)
            yield req

    def train(self, imgs: List[T], batch_size: int = 0, *args, **kwargs):
        p = [image2blob(j) for j in imgs]

        for pi in batch_iterator(p, batch_size):
            req = gnes_pb2.Request()
            for raw_img in pi:
                d = req.train.docs.add()
                d.raw_image.CopyFrom(raw_img)
            yield req
        req = gnes_pb2.Request()
        req.train.flush = True
        yield req

    def query(self, query: T, top_k: int, *args, **kwargs):
        if top_k <= 0:
            raise ValueError('"top_k: %d" is not a valid number' % top_k)

        req = gnes_pb2.Request()
        req.search.query.raw_image.CopyFrom(image2blob(query))
        req.search.top_k = top_k
        yield req
