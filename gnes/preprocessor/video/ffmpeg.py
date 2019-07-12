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

from typing import List
import numpy as np

from .base import BaseVideoPreprocessor
from ...proto import gnes_pb2, array2blob
from ..helper import get_video_frames, phash_descriptor


class FFmpegPreprocessor(BaseVideoPreprocessor):

    def __init__(self,
                 frame_size: str = "192*168",
                 duplicate_rm: bool = True,
                 use_phash_weight: bool = False,
                 phash_thresh: int = 5,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.frame_size = frame_size
        self.phash_thresh = phash_thresh
        self.duplicate_rm = duplicate_rm
        self.use_phash_weight = use_phash_weight

        self._ffmpeg_kwargs = kwargs

    def apply(self, doc: 'gnes_pb2.Document') -> None:
        super().apply(doc)

        # video could't be processed from ndarray!
        # only bytes can be passed into ffmpeg pipeline
        if doc.raw_bytes:
            frames = get_video_frames(
                doc.raw_bytes,
                s=self.frame_size,
                vsync=self._ffmpeg_kwargs.get("vsync", "vfr"),
                vf=self._ffmpeg_kwargs.get("vf", "select=eq(pict_type\\,I)"))

            # remove dupliated key frames by phash value
            if self.duplicate_rm:
                frames = self.duplicate_rm_hash(frames)

            if self.use_phash_weight:
                weight = FFmpegPreprocessor.pic_weight(frames)
            else:
                weight = [1 / len(frames)] * len(frames)

            for ci, chunk in enumerate(frames):
                c = doc.chunks.add()
                c.doc_id = doc.doc_id
                c.blob.CopyFrom(array2blob(chunk))
                c.offset_1d = ci
                c.weight = weight[ci]

        else:
            self.logger.error('bad document: "raw_bytes" is empty!')

    @staticmethod
    def pic_weight(images: List['np.ndarray']) -> List[float]:
        import cv2
        weight = np.zeros([len(images)])
        # n_channel is usually 3 for RGB images
        n_channel = images[0].shape[-1]
        for i, image in enumerate(images):
            weight[i] = sum([
                cv2.calcHist([image], [_], None, [256], [0, 256]).var()
                for _ in range(n_channel)
            ])
        weight = weight / weight.sum()

        # normalized result
        weight = np.exp(-weight * 10)
        return weight / weight.sum()

    def duplicate_rm_hash(self,
                          images: List['np.ndarray']) -> List['np.ndarray']:
        hash_list = [phash_descriptor(_) for _ in images]
        ret = []
        for i, h in enumerate(hash_list):
            flag = 1
            if len(ret) >= 1:
                # only keep images with high phash diff
                # comparing only last kept 9 pics
                for j in range(1, min(len(ret) + 1, 9)):
                    dist = abs(ret[-j][1] - h)
                    if dist < self.phash_thresh:
                        flag = 0
                        break
            if flag:
                ret.append((i, h))

        return [images[_[0]] for _ in ret]
