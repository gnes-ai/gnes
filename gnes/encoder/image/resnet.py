from typing import List

import os
import numpy as np
import torch
import time

from ..base import BaseImageEncoder
from ...proto import gnes_pb2, blob2array
from ...helper import batching


class ResNet(torch.nn.Module):
    def __init__(self, model_dir: str):
        super(ResNet, self).__init__()
        import torchvision.models as models
        os.environ['TORCH_HOME'] = model_dir

        resnet50 = models.resnet50(pretrained=True)
        self.conv1 = resnet50.conv1
        self.bn1 = resnet50.bn1
        self.relu = resnet50.relu

        self.maxpool = resnet50.maxpool
        self.layer1 = resnet50.layer1
        self.layer2 = resnet50.layer2
        self.layer3 = resnet50.layer3
        self.layer4 = resnet50.layer4

        self.avgpool = resnet50.avgpool

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = x.reshape(x.size(0), -1)

        return x


class ResNetEncoder(BaseImageEncoder):
    def __init__(self, model_dir: str, batch_size: int = 64, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.batch_size = batch_size
        self.model_dir = model_dir

        self.is_trained = True
        self._use_cuda = False

    def _post_init(self):
        self._model = ResNet(self.model_dir)
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
            resnet_encodes = self._model(t)
            resnet_encodes = torch.squeeze(resnet_encodes, 0)
            result_npy.append(resnet_encodes.data.cpu().numpy())

        return np.asarray(result_npy, dtype=np.float32)
