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

from ...proto import array2blob

from ..base import BaseVideoPreprocessor
from ..io_utils import video as video_util


class VideoDecoderPreprocessor(BaseVideoPreprocessor):
    store_args_kwargs = True

    def __init__(self,
                 frame_rate: int = 10,
                 frame_size: str = None,
                 vframes: int = -1,
                 drop_raw_data: bool = False,
                 chunk_spliter: str = None,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.frame_rate = frame_rate
        self.frame_size = frame_size
        self.vframes = vframes
        self.drop_raw_data = drop_raw_data
        self.chunk_spliter = chunk_spliter

    def apply(self, doc: 'gnes_pb2.Document') -> None:
        super().apply(doc)
        if doc.WhichOneof('raw_data'):
            video_frames = []
            # raw_type = type(getattr(doc, doc.WhichOneof('raw_data')))
            if doc.raw_bytes:
                video_frames = video_util.capture_frames(
                    input_data=doc.raw_bytes,
                    scale=self.frame_size,
                    fps=self.frame_rate,
                    vframes=self.vframes)
                if not self.drop_raw_data:
                    doc.raw_video.CopyFrom(array2blob(video_frames))
            else:
                self.logger.error('the document "raw_bytes" is empty!')

            if self.chunk_spliter == 'base':
                for i, frame in enumerate(video_frames):
                    c = doc.chunks.add()
                    c.doc_id = doc.doc_id
                    c.blob.CopyFrom(array2blob(frame))
                    c.offset = i
                    c.weight = 1.0
            elif self.chunk_spliter == 'none':
                pass
            elif self.chunk_spliter == 'shot':
                raise NotImplementedError
            else:
                chunk = doc.chunks.add()
                chunk.doc_id = doc.doc_id
                chunk.blob.CopyFrom(array2blob(video_frames))
                chunk.offset = 0
                chunk.weight = 1.0

        else:
            self.logger.error('bad document: "raw_data" is empty!')
