from typing import List

import os
import numpy as np
import torch

from ..base import BaseImageEncoder
from ...proto import gnes_pb2, blob2array
from ...helper import batching


class Vgg(torch.nn.Module):
    def __init__(self, model_dir: str):
        super(Vgg, self).__init__()
        import torchvision.models as models
        os.environ['TORCH_HOME'] = model_dir

        vgg = models.vgg16(pretrained=True)
        self.features = vgg.features
        self.avgpool = vgg.avgpool
        self.classifier = vgg.classifier[0]

    def forward(self, x):
        x = self.features(x)
        x = self.avgpool(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x


class VggEncoder(BaseImageEncoder):
    def __init__(self,  model_dir: str, batch_size: int = 64, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.batch_size = batch_size
        self.model_dir = model_dir

        self.is_trained = True
        self._use_cuda = False

    def _post_init(self):
        self._model = Vgg(self.model_dir)
        self._model = self._model.eval()
        if self._use_cuda:
            # self._model.cuda()
            self._device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
            self._model = self._model.to(self._device)

    @batching()
    def encode(self, img: List['gnes_pb2.blob'], *args, **kwargs) -> np.ndarray:
        self._model.eval()

        img_ = np.stack([blob2array(j) for j in img]).transpose(0, 3, 1, 2)

        img_tensor = torch.from_numpy(img_)
        if self._use_cuda:
            img_tensor = img_tensor.cuda()

        result_npy = []
        for t in img_tensor:
            t = torch.unsqueeze(t, 0)
            vgg_encodes = self._model(t)
            vgg_encodes = torch.squeeze(vgg_encodes, 0)
            result_npy.append(vgg_encodes.data.cpu().numpy())

        return np.asarray(result_npy, dtype=np.float32)
