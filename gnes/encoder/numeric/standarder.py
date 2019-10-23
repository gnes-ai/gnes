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

from ..base import BaseNumericEncoder
from ...helper import batching, train_required


class StandarderEncoder(BaseNumericEncoder):
    batch_size = 2048

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mean = None
        self.scale = None

    def post_init(self):
        from sklearn.preprocessing import StandardScaler
        self.standarder = StandardScaler()

    @batching
    def train(self, vecs: np.ndarray, *args, **kwargs) -> None:
        self.standarder.partial_fit(vecs)

        self.mean = self.standarder.mean_.astype('float32')
        self.scale = self.standarder.scale_.astype('float32')

    @train_required
    @batching
    def encode(self, vecs: np.ndarray, *args, **kwargs) -> np.ndarray:
        return (vecs - self.mean) / self.scale