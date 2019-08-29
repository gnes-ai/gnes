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

from .resize import SizedPreprocessor
from ..helper import get_all_subarea, torch_transform
from ...proto import gnes_pb2, array2blob


class _SlidingPreprocessor(SizedPreprocessor):

    def __init__(self, window_size: int = 64,
                 stride_height: int = 64,
                 stride_wide: int = 64,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.window_size = window_size
        self.stride_height = stride_height
        self.stride_wide = stride_wide

    def apply(self, doc: 'gnes_pb2.Document'):
        super().apply(doc)
        if doc.raw_bytes:
            original_image = Image.open(io.BytesIO(doc.raw_bytes))
            all_subareas, index = get_all_subarea(original_image)
            image_set, center_point_list = self._get_all_sliding_window(np.array(original_image))
            normalized_img_set = [np.array(torch_transform(img)).transpose(1, 2, 0)
                                  for img in image_set]
            weight = self._get_all_chunks_weight(normalized_img_set)

            for ci, ele in enumerate(zip(normalized_img_set, weight)):
                c = doc.chunks.add()
                c.doc_id = doc.doc_id
                c.blob.CopyFrom(array2blob(ele[0]))
                c.offset = ci
                c.offset_nd.extend(self._get_slid_offset_nd(all_subareas, index, center_point_list[ci]))
                c.weight = ele[1]
        else:
            self.logger.error('bad document: "raw_bytes" is empty!')

    def _get_all_sliding_window(self, img: 'np.ndarray'):
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
        center_point_list = [
            [self.window_size / 2 + x * self.stride_wide, self.window_size / 2 + y * self.stride_height]
            for x in range(expanded_input.shape[0])
            for y in range(expanded_input.shape[1])]

        expanded_input = expanded_input.reshape((-1, self.window_size, self.window_size, 3))
        return [np.array(Image.fromarray(img)) for img in expanded_input], center_point_list

    def _get_slid_offset_nd(self, all_subareas: List[List[int]], index: List[List[int]], center_point: List[float]) -> \
            List[int]:
        location_list = self._get_location(all_subareas, center_point)
        location = [i for i in range(len(location_list)) if location_list[i] is True][0]
        return index[location][:2]

    @staticmethod
    def _get_location(all_subareas: List[List[int]], center_point: List[float]) -> List[bool]:
        location_list = []
        x_boundary = max([x[2] for x in all_subareas])
        y_boundary = max([y[3] for y in all_subareas])
        for area in all_subareas:
            if center_point[0] in range(int(area[0]), int(area[2])) and center_point[1] in range(int(area[1]),
                                                                                                 int(area[3])):
                location_list.append(True)
            elif center_point[0] in range(int(area[0]), int(area[2])) and y_boundary == area[3] and center_point[
                1] > y_boundary:
                location_list.append(True)
            elif center_point[1] in range(int(area[1]), int(area[3])) and x_boundary == area[2] and center_point[
                0] > x_boundary:
                location_list.append(True)
            else:
                location_list.append(False)
        if True not in location_list:
            location_list[-1] = True
        return location_list

    def _get_all_chunks_weight(self, normalizaed_image_set):
        raise NotImplementedError


class VanillaSlidingPreprocessor(_SlidingPreprocessor):

    def _get_all_chunks_weight(self, image_set: List['np.ndarray']) -> List[float]:
        return [1 / len(image_set) for _ in range(len(image_set))]


class WeightedSlidingPreprocessor(_SlidingPreprocessor):
    def _get_all_chunks_weight(self, image_set: List['np.ndarray']) -> List[float]:
        from ..video.ffmpeg import FFmpegPreprocessor

        return FFmpegPreprocessor.pic_weight(image_set)
