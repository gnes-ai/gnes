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


from typing import List, Any, Tuple, Union

import numpy as np

from ..base import TrainableBase, CompositionalTrainableBase


class BaseEncoder(TrainableBase):

    def encode(self, data: Any, *args, **kwargs) -> Any:
        pass

    def _copy_from(self, x: 'BaseEncoder') -> None:
        pass


class BaseImageEncoder(BaseEncoder):

    def encode(self, img: List['np.ndarray'], *args, **kwargs) -> np.ndarray:
        pass


class BaseVideoEncoder(BaseEncoder):

    def encode(self, data: List['np.ndarray'], *args, **kwargs) -> Union[np.ndarray, List['np.ndarray']]:
        pass


class BaseTextEncoder(BaseEncoder):

    def encode(self, text: List[str], *args, **kwargs) -> Union[Tuple, np.ndarray]:
        pass


class BaseNumericEncoder(BaseEncoder):

    def encode(self, data: np.ndarray, *args, **kwargs) -> np.ndarray:
        pass


class BaseAudioEncoder(BaseEncoder):

    def encode(self, data: List['np.ndarray'], *args, **kwargs) -> np.ndarray:
        pass


class BaseBinaryEncoder(BaseEncoder):

    def encode(self, data: np.ndarray, *args, **kwargs) -> bytes:
        if data.dtype != np.uint8:
            raise ValueError('data must be np.uint8 but received %s' % data.dtype)
        return data.tobytes()


class PipelineEncoder(CompositionalTrainableBase):
    def encode(self, data: Any, *args, **kwargs) -> Any:
        if not self.components:
            raise NotImplementedError
        for be in self.components:
            data = be.encode(data, *args, **kwargs)
        return data

    def train(self, data, *args, **kwargs):
        if not self.components:
            raise NotImplementedError
        for idx, be in enumerate(self.components):
            if not be.is_trained:
                be.train(data, *args, **kwargs)

            if idx + 1 < len(self.components):
                data = be.encode(data, *args, **kwargs)
