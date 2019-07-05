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

import re

from .base import BaseTextPreprocessor
from ...proto import gnes_pb2


class TextPreprocessor(BaseTextPreprocessor):
    def __init__(self, deliminator: str = r'[.。！？!?]+', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.deliminator = deliminator

    def apply(self, doc: 'gnes_pb2.Document') -> None:
        super().apply(doc)
        doc.raw_text = doc.raw_bytes.decode().strip()
        for ci, s in enumerate(re.split(self.deliminator, doc.raw_text)):
            if s.strip():
                c = doc.chunks.add()
                c.doc_id = doc.doc_id
                c.text = s.strip()
                c.offset_1d = ci
                c.weight = len(c.text) / len(doc.raw_text)
