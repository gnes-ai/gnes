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
from PIL import Image

from ..base import BaseImagePreprocessor
from ...proto import gnes_pb2, blob2array, array2blob


class SizedPreprocessor(BaseImagePreprocessor):
    def __init__(self,
                 target_width: int = 224,
                 target_height: int = 224,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_width = target_width
        self.target_height = target_height


class ResizeChunkPreprocessor(SizedPreprocessor):

    def apply(self, doc: 'gnes_pb2.Document') -> None:
        super().apply(doc)
        for c in doc.chunks:
            img = blob2array(c.blob)
            img = np.array(Image.fromarray(img.astype('uint8')).resize((self.target_width, self.target_height)))
            c.blob.CopyFrom(array2blob(img))
