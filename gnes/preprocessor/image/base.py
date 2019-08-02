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

from ..base import BasePreprocessor
from ...proto import gnes_pb2


class BaseImagePreprocessor(BasePreprocessor):
    doc_type = gnes_pb2.Document.IMAGE

    def __init__(self,
                 target_img_size: int = 224,
                 is_rgb: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_img_size = target_img_size
        self.is_rgb = is_rgb

    def _get_all_chunks_weight(self, image_set: List['np.ndarray']) -> List[float]:
        pass

    @staticmethod
    def _torch_transform(image):
        import torchvision.transforms as transforms
        return transforms.Compose([transforms.ToTensor(),
                                   transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))])(image)

    @staticmethod
    def _get_all_subarea(image):
        from itertools import product
        x_list = [0, image.size[0] / 3, 2 * image.size[0] / 3, image.size[0]]
        y_list = [0, image.size[1] / 3, 2 * image.size[1] / 3, image.size[1]]

        index = [[x, y, x + 1, y + 1] for [x, y] in product(range(len(x_list) - 1), range(len(y_list) - 1))]
        all_subareas = [[x_list[idx[0]], y_list[idx[1]], x_list[idx[2]], y_list[idx[3]]] for idx in index]
        return all_subareas, index
