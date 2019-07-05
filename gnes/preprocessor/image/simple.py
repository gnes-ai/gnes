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
from ...proto import gnes_pb2, array2blob


class SlidingPreprocessor(BaseImagePreprocessor):

    def __init__(self, slide_window_ratio: float = 2 / 3,
                 num_hwindow: int = 1,
                 num_vwindow: int = 1,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.slide_window_ratio = slide_window_ratio
        self.num_hwindow = num_hwindow
        self.num_vwindow = num_vwindow

    def apply(self, doc: 'gnes_pb2.Document'):
        super().apply(doc)
        img = np.array(Image.open(io.BytesIO(doc.raw_bytes)))
        image_set = self._get_all_sliding_window(img)
        for ci, chunk in enumerate(image_set):
            c = doc.chunks.add()
            c.doc_id = doc.doc_id
            c.blob.CopyFrom(array2blob(chunk))
            c.offset_1d = ci
            c.weight = 1 / len(image_set)

    def _get_all_sliding_window(self, img: 'np.ndarray') -> List['np.ndarray']:
        chunk_list = []
        wide, height = img.size

        # area of cropped image
        box_wide = self.slide_window_ratio * wide
        box_height = self.slide_window_ratio * height

        # stride for two directions
        # number of chunks after cropping: (wide_time + 1) * (height_time + 1)

        stride_wide = (wide - box_wide) / self.num_hwindow
        stride_height = (height - box_height) / self.num_vwindow

        # initialization
        left = 0
        right = box_wide
        top = 0
        bottom = box_height

        for i in range(self.num_vwindow + 1):
            for j in range(self.num_hwindow + 1):
                area = (left, top, right, bottom)
                cropped_img = np.asarray(img.crop(area).resize((self.target_img_size, self.target_img_size)),
                                         dtype=np.float32)

                blob_cropped_img = gnes_pb2.NdArray()
                blob_cropped_img.data = cropped_img.tobytes()
                blob_cropped_img.shape.extend(cropped_img.shape)
                blob_cropped_img.dtype = cropped_img.dtype.name

                chunk_list.append(blob_cropped_img)
                left += stride_wide
                right += stride_wide
            left = 0
            right = box_wide
            top += stride_height
            bottom += stride_height
        return chunk_list


class SegmentPreprocessor(BaseImagePreprocessor):
    def apply(self, doc: 'gnes_pb2.Document'):
        raise NotImplementedError
