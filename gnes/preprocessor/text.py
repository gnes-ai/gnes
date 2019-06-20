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
import random
import re
from typing import TextIO, List

from .base import BasePreprocessor
from ..proto import gnes_pb2


class TextPreprocessor(BasePreprocessor):
    def __init__(self, start_doc_id: int = 0,
                 random_doc_id: bool = True,
                 deliminator: str = r'[.。！？!?]+', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_doc_id = start_doc_id
        self.random_doc_id = random_doc_id
        self.deliminator = deliminator
        self.is_trained = True

    def apply(self, batch_data: List[gnes_pb2.Document]) -> List['gnes_pb2.Document']:
        # each str in batch_data will be transformed to a document
        data = [d.raw_text for d in batch_data if d.raw_text.strip()]
        docs = []
        for doc_id, doc_txt in enumerate(data, self.start_doc_id):
            doc = self._line2pb_doc(doc_txt,
                                    doc_id if not self.random_doc_id else random.randint(0, ctypes.c_uint(-1).value))
            docs.append(doc)
        return docs

    def _line2pb_doc(self, line: str, doc_id: int) -> 'gnes_pb2.Document':
        doc = gnes_pb2.Document()
        doc.doc_id = doc_id
        doc.doc_type = gnes_pb2.Document.TEXT
        # depending on whether deliminator is enabled or not
        # the generated document could have multiple chunks or just one chunk
        if self.deliminator:
            for ci, s in enumerate(re.split(self.deliminator, line)):
                if s.strip():
                    c = doc.chunks.add()
                    c.doc_id = doc_id
                    c.text = s
                    c.offset_1d = ci
        else:
            c = doc.chunks.add()
            c.doc_id = doc_id
            c.text = line
            c.offset_1d = 0
        return doc


## depreciated!!! useless for now
def txt_file2pb_docs(fp: TextIO, start_id: int = 0) -> List['gnes_pb2.Document']:
    data = [v for v in fp if v.strip()]
    docs = []
    for doc_id, doc_txt in enumerate(data, start_id):
        doc = line2pb_doc(doc_txt, doc_id)
        docs.append(doc)
    return docs


## depreciated!!! useless for now
def line2pb_doc(line: str, doc_id: int = 0, deliminator: str = r'[.。！？!?]+') -> 'gnes_pb2.Document':
    doc = gnes_pb2.Document()
    doc.doc_id = doc_id
    doc.doc_type = gnes_pb2.Document.TEXT
    doc.meta_info = line.encode()
    if deliminator:
        for ci, s in enumerate(re.split(deliminator, line)):
            if s.strip():
                c = doc.chunks.add()
                c.doc_id = doc_id
                c.text = s
                c.offset_1d = ci
    else:
        c = doc.chunks.add()
        c.doc_id = doc_id
        c.text = line
        c.offset_1d = 0
    return doc
