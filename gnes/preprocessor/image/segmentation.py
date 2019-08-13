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
import os
from typing import List

import numpy as np
from PIL import Image

from .base import BaseImagePreprocessor
from ...proto import array2blob


class SegmentPreprocessor(BaseImagePreprocessor):

    def __init__(self, model_name: str,
                 model_dir: str,
                 _use_cuda: bool = False,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.model_dir = model_dir
        self._use_cuda = _use_cuda

    def post_init(self):
        import torch
        import torchvision.models as models

        os.environ['TORCH_HOME'] = self.model_dir
        self._model = getattr(models.detection, self.model_name)(pretrained=True)
        self._model = self._model.eval()
        if self._use_cuda:
            # self._model.cuda()
            self._device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
            self._model = self._model.to(self._device)

    def apply(self, doc: 'gnes_pb2.Document'):
        super().apply(doc)
        if doc.raw_bytes:
            original_image = Image.open(io.BytesIO(doc.raw_bytes))
            all_subareas, index = self._get_all_subarea(original_image)
            image_tensor = self._torch_transform(original_image)
            if self._use_cuda:
                image_tensor = image_tensor.cuda()

            seg_output = self._model([image_tensor])

            weight = seg_output[0]['scores'].tolist()
            length = len(list(filter(lambda x: x >= 0.5, weight)))
            chunks = seg_output[0]['boxes'].tolist()[:length]
            weight = weight[:length]

            for ci, ele in enumerate(zip(chunks, weight)):
                c = doc.chunks.add()
                c.doc_id = doc.doc_id
                c.blob.CopyFrom(array2blob(self._crop_resize(original_image, ele[0])))
                c.offset_1d = ci
                c.offset_nd.x.extend(self._get_seg_offset_nd(all_subareas, index, ele[0]))
                c.weight = self._cal_area(ele[0]) / (original_image.size[0] * original_image.size[1])

            c = doc.chunks.add()
            c.doc_id = doc.doc_id
            c.blob.CopyFrom(array2blob(np.array(original_image.resize((self.target_img_size,
                                                                       self.target_img_size)))))
            c.offset_1d = len(chunks)
            c.offset_nd.x.extend([100, 100])
            c.weight = 1.
        else:
            self.logger.error('bad document: "raw_bytes" is empty!')

    def _crop_resize(self, original_image, coordinates):
        return np.array(original_image.crop(coordinates).resize((self.target_img_size,
                                                                 self.target_img_size)))

    def _get_seg_offset_nd(self, all_subareas: List[List[int]], index: List[List[int]], chunk: List[int]) -> List[int]:
        iou_list = [self._cal_iou(area, chunk) for area in all_subareas]
        return index[int(np.argmax(iou_list))][:2]

    @staticmethod
    def _cal_area(coordinate: List[int]):
        return (coordinate[2] - coordinate[0]) * (coordinate[3] - coordinate[1])

    def _cal_iou(self, image: List[int], chunk: List[int]) -> float:
        chunk_area = self._cal_area(chunk)
        image_area = self._cal_area(image)

        x1 = max(chunk[0], image[0])
        y1 = max(chunk[1], image[1])
        x2 = min(chunk[2], image[2])
        y2 = min(chunk[3], image[3])

        overlap_area = max(0, x2 - x1) * max(0, y2 - y1)
        iou = overlap_area / (chunk_area + image_area - overlap_area)
        return iou
