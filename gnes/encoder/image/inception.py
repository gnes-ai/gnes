from typing import List

import torch
import torch.nn.functional as F
import numpy as np
import os

from ..base import BaseImageEncoder
from ...proto import gnes_pb2, blob2array
from ...helper import batching


class Inception(torch.nn.Module):
    def __init__(self, model_dir: str):
        super(Inception, self).__init__()
        import torchvision.models as models
        os.environ['TORCH_HOME'] = model_dir

        inception = models.inception_v3(pretrained=True)
        self.Conv2d_1a_3x3 = inception.Conv2d_1a_3x3
        self.Conv2d_2a_3x3 = inception.Conv2d_2a_3x3
        self.Conv2d_2b_3x3 = inception.Conv2d_2b_3x3

        self.Conv2d_3b_1x1 = inception.Conv2d_3b_1x1
        self.Conv2d_4a_3x3 = inception.Conv2d_4a_3x3
        self.Mixed_5b = inception.Mixed_5b
        self.Mixed_5c = inception.Mixed_5c
        self.Mixed_5d = inception.Mixed_5d

        self.Mixed_6a = inception.Mixed_6a
        self.Mixed_6b = inception.Mixed_6b
        self.Mixed_6c = inception.Mixed_6c
        self.Mixed_6d = inception.Mixed_6d
        self.Mixed_6e = inception.Mixed_6e

        self.Mixed_7a = inception.Mixed_7a
        self.Mixed_7b = inception.Mixed_7b
        self.Mixed_7c = inception.Mixed_7c

        self.training = inception.training

    def forward(self, x):
        # N x 3 x 299 x 299
        x = self.Conv2d_1a_3x3(x)
        # N x 32 x 149 x 149
        x = self.Conv2d_2a_3x3(x)
        # N x 32 x 147 x 147
        x = self.Conv2d_2b_3x3(x)
        # N x 64 x 147 x 147
        x = F.max_pool2d(x, kernel_size=3, stride=2)
        # N x 64 x 73 x 73
        x = self.Conv2d_3b_1x1(x)
        # N x 80 x 73 x 73
        x = self.Conv2d_4a_3x3(x)
        # N x 192 x 71 x 71
        x = F.max_pool2d(x, kernel_size=3, stride=2)
        # N x 192 x 35 x 35
        x = self.Mixed_5b(x)
        # N x 256 x 35 x 35
        x = self.Mixed_5c(x)
        # N x 288 x 35 x 35
        x = self.Mixed_5d(x)
        # N x 288 x 35 x 35
        x = self.Mixed_6a(x)
        # N x 768 x 17 x 17
        x = self.Mixed_6b(x)
        # N x 768 x 17 x 17
        x = self.Mixed_6c(x)
        # N x 768 x 17 x 17
        x = self.Mixed_6d(x)
        # N x 768 x 17 x 17
        x = self.Mixed_6e(x)
        # N x 768 x 17 x 17
        x = self.Mixed_7a(x)
        # N x 1280 x 8 x 8
        x = self.Mixed_7b(x)
        # N x 2048 x 8 x 8
        x = self.Mixed_7c(x)
        # N x 2048 x 8 x 8
        # Adaptive average pooling
        x = F.adaptive_avg_pool2d(x, (1, 1))
        # N x 2048 x 1 x 1
        x = F.dropout(x, training=self.training)
        # N x 2048 x 1 x 1
        x = x.view(x.size(0), -1)
        # N x 2048

        return x


class InceptionEncoder(BaseImageEncoder):
    def __init__(self, model_dir: str, batch_size: int = 64, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.batch_size = batch_size
        self.model_dir = model_dir

        self.is_trained = True
        self._use_cuda = False

    def _post_init(self):
        self._model = Inception(self.model_dir)
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
            inception_encodes = self._model(t)
            inception_encodes = torch.squeeze(inception_encodes, 0)
            result_npy.append(inception_encodes.data.cpu().numpy())

        return np.asarray(result_npy, dtype=np.float32)

