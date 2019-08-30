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

import numpy as np

from ..base import BaseAudioPreprocessor
from ...proto import array2blob
from ..io_utils.audio import split_audio


class AudioVanilla(BaseAudioPreprocessor):

    def __init__(self,
                 sample_rate: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sample_rate = sample_rate

    def apply(self, doc: 'gnes_pb2.Document') -> None:
        super().apply(doc)

        if doc.raw_bytes:
            audio = split_audio(input_data=doc.raw_bytes, sample_rate=self.sample_rate)
            if len(audio) >= 1:
                for ci, chunks in enumerate(audio):
                    c = doc.chunks.add()
                    c.doc_id = doc.doc_id
                    c.blob.CopyFrom(array2blob(np.array(chunks, dtype=np.float32)))
                    c.offset = ci
                    c.weight = 1 / len(audio)
            else:
                self.logger.warning('bad document: no audio extracted')
        else:
            self.logger.error('bad document: "raw_bytes" is empty!')
