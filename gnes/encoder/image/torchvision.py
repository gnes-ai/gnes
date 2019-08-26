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
from ...helper import batching, as_numpy_array


class TorchvisionEncoder(BaseImageEncoder):
    batch_size = 64

    def __init__(self, model_name: str,
                 layers: List[str],
                 model_dir: str,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model_dir = model_dir
        self.model_name = model_name
        self.layers = layers

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
                    layer = 'm.%s(x)' % layer
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
        if self.on_gpu:
            # self._model.cuda()
            self._device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
            self._model = self._model.to(self._device)

    def encode(self, img: List['np.ndarray'], *args, **kwargs) -> np.ndarray:
        import torch
        self._model.eval()

        # padding to ensure that every chunk has the same number of frame
        def _padding(img: List['np.ndarray']):
            max_lenth = max([len(x) for x in img])
            img = [np.concatenate((im, np.zeros((max_lenth - im.shape[0], im.shape[1], im.shape[2], 3), dtype=np.uint8))
                                  , axis=0)
                   if im.shape[0] < max_lenth else im for im in img]
            return img, max_lenth

        # for video
        if len(img[0].shape) == 4:
            img, max_lenth = _padding(img)
        # for image
        else:
            max_lenth = -1

        @batching(chunk_dim=max_lenth)
        @as_numpy_array
        def _encode(_, img: List['np.ndarray']):
            import copy

            if len(img[0].shape) == 4:
                img_ = copy.deepcopy(img)
                img_ = np.concatenate((list(img_[i] for i in range(len(img_)))), axis=0)

                img_for_torch = np.array(img_, dtype=np.float32).transpose(0, 3, 1, 2)
            else:
                img_for_torch = np.array(img, dtype=np.float32).transpose(0, 3, 1, 2)

            img_tensor = torch.from_numpy(img_for_torch)
            if self.on_gpu:
                img_tensor = img_tensor.cuda()

            encodes = self._model(img_tensor)

            return encodes.data.cpu()

        return _encode(self, img)
