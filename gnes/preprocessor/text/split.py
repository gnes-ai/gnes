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

import json
import re
import string

from ..base import BaseTextPreprocessor
from ...proto import gnes_pb2


class SentSplitPreprocessor(BaseTextPreprocessor):
    def __init__(self,
                 min_sent_len: int = 1,
                 max_sent_len: int = 256,
                 deliminator: str = '.!?。！？',
                 is_json: bool = False,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_sent_len = min_sent_len
        self.max_sent_len = max_sent_len
        self.deliminator = deliminator
        self.is_json = is_json

    def apply(self, doc: 'gnes_pb2.Document') -> None:
        super().apply(doc)
        d = doc.raw_bytes.decode()
        if self.is_json:
            d = json.loads(d)
            doc.raw_text = d.pop('Content')
            doc.meta_info = json.dumps(d).encode()
        else:
            doc.raw_text = d

        ret = [(m.group(0), m.start(), m.end()) for m in
               re.finditer(r'[^{0}]+[{0}]'.format(self.deliminator), doc.raw_text)]
        for ci, (r, s, e) in enumerate(ret):
            f = ''.join(filter(lambda x: x in string.printable, r))
            f = re.sub('\n+', ' ', f).strip()
            if len(f) > self.min_sent_len:
                c = doc.chunks.add()
                c.doc_id = doc.doc_id
                c.text = f[:self.max_sent_len]
                c.offset = ci
                c.weight = len(c.text) / len(doc.raw_text)
                c.offset_nd.extend([s, e])
