from typing import List, TypeVar
import numpy as np

from ..base import BaseRequestGenerator
from ... import gnes_pb2
from ....helper import batch_iterator

T = TypeVar('T', bound='PIL.Image')


class ImageRequestGenerator(BaseRequestGenerator):
    def index(self, imgs: List[T], batch_size: int = 0, *args, **kwargs):
        p = []
        for img in imgs:
            p.append(self.Image2blob(img))

        for pi in batch_iterator(p, batch_size):
            req = gnes_pb2.Request()
            for raw_img in pi:
                d = req.index.docs.add()
                d.raw_image.CopyFrom(raw_img)
            yield req

    def train(self, imgs: List[T], batch_size: int = 0, *args, **kwargs):
        p = []
        for img in imgs:
            p.append(self.Image2blob(img))

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

        raw_img = self.Image2blob(query)

        req = gnes_pb2.Request()
        req.search.query.raw_image.CopyFrom(raw_img)
        req.search.top_k = top_k
        yield req

    def Image2blob(self, img: T):
        image_asarray = np.asarray(img, dtype=np.float32)
        blob = gnes_pb2.NdArray()
        blob.data = image_asarray.tobytes()
        blob.shape.extend(image_asarray.shape)
        blob.dtype = image_asarray.dtype.name
        return blob

