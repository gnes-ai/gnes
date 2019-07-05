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

import ctypes
import random

import numpy as np
from PIL import Image

from ..base import BasePreprocessor
from ...proto import gnes_pb2


class ImagePreprocessor(BasePreprocessor):
    def __init__(self, start_doc_id: int = 0,
                 random_doc_id: bool = True,
                 target_img_size: int = 224,
                 segmentation: str = 'stride',
                 is_rgb: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_doc_id = start_doc_id
        self.random_doc_id = random_doc_id
        self.target_img_size = target_img_size
        self.segmentation = segmentation
        self.is_rgb = is_rgb

    def apply(self, doc: 'gnes_pb2.Document'):
        doc.doc_id = self.start_doc_id if not self.random_doc_id else random.randint(0, ctypes.c_uint(-1).value)
        doc.doc_type = gnes_pb2.Document.IMAGE
        if self.is_rgb:
            image_asarray = np.frombuffer(doc.raw_image.data, dtype=np.float32).reshape(doc.raw_image.shape[0],
                                                                                        doc.raw_image.shape[1], 3)
        else:
            image_asarray = np.frombuffer(doc.raw_image.data, dtype=np.float32).reshape(doc.raw_image.shape[0],
                                                                                        doc.raw_image.shape[1], 1)

        raw_img = Image.fromarray(np.uint8(image_asarray))
        if self.segmentation:
            image_set = self._segment_image(raw_img)
            for ci, chunk in enumerate(image_set):
                c = doc.chunks.add()
                c.doc_id = doc.doc_id
                c.blob.CopyFrom(chunk)
                # c.offset_nd = ci
                c.weight = 1 / len(image_set)
        else:
            c = doc.chunks.add()
            c.doc_id = doc.doc_id
            c.blob.CopyFrom(doc.raw_image)
            # c.offset_nd = 0
            c.weight = 1.
        return doc

    def _segment_image(self, img: Image):
        if self.segmentation == 'stride':
            return self._crop_img(img)
        elif self.segmentation == 'bounding-box':
            return self._seg_img(img)
        else:
            raise ValueError(
                'split_method: %s has not been implemented' % self.segmentation)

    def _crop_img(self, img: Image):
        chunk_list = []
        wide, height = img.size

        # area of cropped image
        crop_ratio = 2 / 3
        box_wide = crop_ratio * wide
        box_height = crop_ratio * height

        # stride for two directions
        # number of chunks after cropping: (wide_time + 1) * (height_time + 1)
        wide_time = 1
        height_time = 1

        stride_wide = (wide - box_wide) / wide_time
        stride_height = (height - box_height) / height_time

        # initialization
        left = 0
        right = box_wide
        top = 0
        bottom = box_height

        for i in range(height_time + 1):
            for j in range(wide_time + 1):
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

    def _seg_img(self, img):
        pass
