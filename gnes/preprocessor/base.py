#  Tencent is pleased to support the open source community by making GNES available.
#
#  Copyright (C) 2019 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# pylint: disable=low-comment-ratio
import ctypes
import io
import random

import numpy as np
from PIL import Image

from ..base import TrainableBase
from ..proto import gnes_pb2, array2blob


class BasePreprocessor(TrainableBase):
    doc_type = gnes_pb2.Document.UNKNOWN

    def __init__(self, start_doc_id: int = 0, random_doc_id: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_doc_id = start_doc_id
        self.random_doc_id = random_doc_id

    def apply(self, doc: 'gnes_pb2.Document') -> None:
        doc.doc_id = self.start_doc_id if not self.random_doc_id else random.randint(0, ctypes.c_uint(-1).value)
        doc.doc_type = self.doc_type


class BaseSingletonPreprocessor(BasePreprocessor):

    def __init__(self, doc_type: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_img_size = 224
        self.is_trained = True
        self.doc_type = doc_type

    def apply(self, doc: 'gnes_pb2.Document'):
        super().apply(doc)
        c = doc.chunks.add()
        c.doc_id = doc.doc_id
        c.offset_1d = 0
        c.weight = 1.
        if doc.raw_bytes:
            self.raw_to_chunk(c, doc.raw_bytes)
        else:
            self.logger.error('bad document: "raw_bytes" is empty!')

    def raw_to_chunk(self, chunk: 'gnes_pb2.Chunk', raw_bytes: bytes):
        if self.doc_type == gnes_pb2.Document.TEXT:
            chunk.text = raw_bytes.decode()
        elif self.doc_type == gnes_pb2.Document.IMAGE:
            img = np.array(Image.open(io.BytesIO(raw_bytes)))
            img = np.array(Image.fromarray(img).resize((self.target_img_size, self.target_img_size)))
            chunk.blob.CopyFrom(array2blob(img))
        elif self.doc_type == gnes_pb2.Document.VIDEO:
            raise NotImplementedError
        else:
            raise NotImplementedError
