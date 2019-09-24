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
from typing import List

from gnes.preprocessor.base import BaseVideoPreprocessor
from gnes.proto import gnes_pb2, array2blob
from gnes.preprocessor.io_utils import video


class VideoDecodePreprocessor(BaseVideoPreprocessor):
    store_args_kwargs = True

    def __init__(self,
                 frame_rate: int = 10,
                 vframes: int = -1,
                 scale: str = None,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.frame_rate = frame_rate
        self.vframes = vframes
        self.scale = scale

    def apply(self, doc: 'gnes_pb2.Document') -> None:
        super().apply(doc)

        if doc.raw_bytes:
            all_frames = video.capture_frames(
                input_data=doc.raw_bytes,
                scale=self.scale,
                fps=self.frame_rate,
                vframes=self.vframes)

            c = doc.chunks.add()
            c.doc_id = doc.doc_id
            c.blob.CopyFrom(array2blob(all_frames))
            c.offset = 0
            c.weight = 1.0
        else:
            self.logger.error('bad document: "raw_bytes" is empty!')
