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

from typing import Generator

from .base import BaseMapRouter
from ..helper import batch_iterator
from ..proto import gnes_pb2


class PublishRouter(BaseMapRouter):

    def __init__(self, num_part: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_part = num_part

    def apply(self, msg: 'gnes_pb2.Message', *args, **kwargs) -> Generator:
        msg.envelope.num_part.append(self.num_part)


class DocBatchRouter(BaseMapRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
                _msg.envelope.num_part.append(num_part)
                yield _msg
