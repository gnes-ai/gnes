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

import os
from typing import List, Callable

import numpy as np

from ..base import BaseImageEncoder
from ...helper import batching


class BasePytorchEncoder(BaseImageEncoder):

    def __init__(self, model_name: str,
                 layers: List[str],
                 model_dir: str,
                 batch_size: int = 64,
                 use_cuda: bool = False,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.batch_size = batch_size
        self.model_dir = model_dir
        self.model_name = model_name
        self.layers = layers
        self._use_cuda = use_cuda

    def post_init(self):
        import torch
        import torchvision.models as models

        class _Model(torch.nn.Module):
            def __init__(self, model_name: str, layers: List[str]):
                super().__init__()

                self.m = getattr(models, model_name)(pretrained=True)
                self.layers = [self.fn_parser(l) for l in layers]

            def fn_parser(self, layer: str) -> Callable:

                if '(' not in layer and ')' not in layer:
                    # this is a shorthand syntax we need to add "(x)" at the end
                    layer = 'm.%s(x)'%layer
                else:
                    pass

                def layer_fn(x, l, m, torch):
                    return eval(l)
                return lambda x: layer_fn(x, layer, self.m, torch)

            def forward(self, x):
                for l in self.layers:
                    x = l(x)
                return x

        os.environ['TORCH_HOME'] = self.model_dir
        self._model = _Model(self.model_name, self.layers)
        self._model = self._model.eval()
        if self._use_cuda:
            # self._model.cuda()
            self._device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
            self._model = self._model.to(self._device)

    @batching
    def encode(self, img: List['np.ndarray'], *args, **kwargs) -> np.ndarray:
        import torch
        self._model.eval()

        img_ = np.array(img, dtype=np.float32).transpose(0, 3, 1, 2)

        img_tensor = torch.from_numpy(img_)
        if self._use_cuda:
            img_tensor = img_tensor.cuda()

        result_npy = []
        for t in img_tensor:
            t = torch.unsqueeze(t, 0)
            encodes = self._model(t)
            encodes = torch.squeeze(encodes, 0)
            result_npy.append(encodes.data.cpu().numpy())

        return np.array(result_npy, dtype=np.float32)

