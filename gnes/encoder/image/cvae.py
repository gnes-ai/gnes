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
import numpy as np
from gnes.helper import batch_iterator
from ..base import BaseImageEncoder
from PIL import Image


class CVAEEncoder(BaseImageEncoder):

    def __init__(self, model_dir: str,
                 latent_dim: int = 300,
                 batch_size: int = 64,
                 select_method: str = 'MEAN',
                 use_gpu: bool = True,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model_dir = model_dir
        self.latent_dim = latent_dim
        self.batch_size = batch_size
        self.select_method = select_method
        self.use_gpu = use_gpu

    def post_init(self):
        import tensorflow as tf
        from .cave_cores.model import CVAE

        self._model = CVAE(self.latent_dim)
        self.inputs = tf.placeholder(tf.float32,
                                     (None, 120, 120, 3))

        self.mean, self.var = self._model.encode(self.inputs)

        config = tf.ConfigProto(log_device_placement=False)
        if self.use_gpu:
            config.gpu_options.allow_growth = True
        self.sess = tf.Session(config=config)
        self.saver = tf.train.Saver()
        self.saver.restore(self.sess, self.model_dir)

    def encode(self, img: List['np.ndarray'], *args, **kwargs) -> np.ndarray:
        ret = []
        img = [(np.array(Image.fromarray(im).resize((120, 120)),
                dtype=np.float32)/255) for im in img]
        for _im in batch_iterator(img, self.batch_size):
            _mean, _var = self.sess.run((self.mean, self.var),
                                        feed_dict={self.inputs: _im})
            if self.select_method == 'MEAN':
                ret.append(_mean)
            elif self.select_method == 'VAR':
                ret.append(_var)
            elif self.select_method == 'MEAN_VAR':
                ret.append(np.concatenate([_mean, _var]), axis=1)
        return np.concatenate(ret, axis=0).astype(np.float32)
