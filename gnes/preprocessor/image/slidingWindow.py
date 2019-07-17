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
import io
from typing import List

import numpy as np
from PIL import Image

from .base import BaseImagePreprocessor
from ..video.ffmpeg import FFmpegPreprocessor
from ...proto import gnes_pb2, array2blob


class BaseSlidingPreprocessor(BaseImagePreprocessor):

    def __init__(self, window_size: int = 64,
                 stride_height: int = 64,
                 stride_wide: int = 64,
                 target_img_size: int = 224,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.window_size = window_size
        self.stride_height = stride_height
        self.stride_wide = stride_wide
        self.target_img_size = target_img_size

    def apply(self, doc: 'gnes_pb2.Document'):
        super().apply(doc)
        if doc.raw_bytes:
            img = np.array(Image.open(io.BytesIO(doc.raw_bytes)))
            image_set = self._get_all_sliding_window(img)
            normalizaed_image_set = [np.array(self._torch_transform(img)).transpose(1, 2, 0)
                                     for img in image_set]
            weight = self._get_all_chunks_weight(normalizaed_image_set)

            for ci, ele in enumerate(zip(normalizaed_image_set, weight)):
                c = doc.chunks.add()
                c.doc_id = doc.doc_id
                c.blob.CopyFrom(array2blob(ele[0]))
                c.offset_1d = ci
                c.weight = ele[1]
        else:
            self.logger.error('bad document: "raw_bytes" is empty!')

    def _get_all_sliding_window(self, img: 'np.ndarray') -> List['np.ndarray']:
        extend_height = self.window_size - (img.shape[0]) % self.stride_height
        extend_wide = self.window_size - (img.shape[1]) % self.stride_wide

        input = np.pad(img, ((0, extend_height),
                             (0, extend_wide),
                             (0, 0)),
                       mode='constant', constant_values=0)
        expanded_input = np.lib.stride_tricks.as_strided(
            input,
            shape=(
                1 + int((input.shape[0] - self.window_size) / self.stride_height),
                1 + int((input.shape[1] - self.window_size) / self.stride_wide),
                self.window_size,
                self.window_size,
                3
            ),
            strides=(
                input.strides[0] * self.stride_height,
                input.strides[1] * self.stride_wide,
                input.strides[0],
                input.strides[1],
                1
            ),
            writeable=False
        )
        expanded_input = expanded_input.reshape((-1, self.window_size, self.window_size, 3))
        return [np.array(Image.fromarray(img).resize((self.target_img_size, self.target_img_size))) for img in expanded_input]


class VanillaSlidingPreprocessor(BaseSlidingPreprocessor):

    def _get_all_chunks_weight(self, image_set: List['np.ndarray']) -> List[float]:
        return [1 / len(image_set) for _ in range(len(image_set))]


class WeightedSlidingPreprocessor(BaseSlidingPreprocessor):

    def _get_all_chunks_weight(self, image_set: List['np.ndarray']) -> List[float]:
        return FFmpegPreprocessor.pic_weight(image_set)

