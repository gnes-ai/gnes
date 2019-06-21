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
from ..service.base import ServiceError


class TextPreprocessor(BasePreprocessor):
    def __init__(self, start_doc_id: int = 0,
                 random_doc_id: bool = True,
                 deliminator: str = r'[.。！？!?]+',
                 do_strip: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_doc_id = start_doc_id
        self.random_doc_id = random_doc_id
        self.deliminator = deliminator
        self.do_strip = do_strip
        self.is_trained = True

    def apply(self, doc: 'gnes_pb2.Document'):
        doc.doc_id = self.start_doc_id if not self.random_doc_id else random.randint(0, ctypes.c_uint(-1).value)
        doc.doc_type = gnes_pb2.Document.TEXT
        raw_text = doc.raw_text.strip() if self.do_strip else doc.raw_text
        if raw_text:
            if self.deliminator:
                for ci, s in enumerate(re.split(self.deliminator, raw_text)):
                    if s.strip():
                        c = doc.chunks.add()
                        c.doc_id = doc.doc_id
                        c.text = s.strip()
                        c.offset_1d = ci
            else:
                c = doc.chunks.add()
                c.doc_id = doc.doc_id
                c.text = raw_text
                c.offset_1d = 0
        else:
            raise ServiceError('"raw_text" is empty string after striping, not allowed!')


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
