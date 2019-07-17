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
from ...helper import batching
from PIL import Image


class TFInceptionEncoder(BaseImageEncoder):

    def __init__(self, model_dir: str,
                 batch_size: int = 64,
                 select_layer: str = 'PreLogitsFlatten',
                 use_cuda: bool = False,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model_dir = model_dir
        self.batch_size = batch_size
        self.select_layer = select_layer
        self._use_cuda = use_cuda
        self.inception_size_x = 299
        self.inception_size_y = 299

    def post_init(self):
        import tensorflow as tf
        from gnes.encoder.image.inception_cores.inception_v4 import inception_v4
        from gnes.encoder.image.inception_cores.inception_utils import inception_arg_scope

        arg_scope = inception_arg_scope()
        inception_v4.default_image_size = self.inception_size_x
        self.inputs = tf.placeholder(tf.float32, (None,
                                                  self.inception_size_x,
                                                  self.inception_size_y, 3))

        with tf.contrib.slim.arg_scope(arg_scope):
            self.logits, self.end_points = inception_v4(self.inputs,
                                                        is_training=False,
                                                        dropout_keep_prob=1.0)

        config = tf.ConfigProto(log_device_placement=False)
        if self._use_cuda:
            config.gpu_options.allow_growth = True
        self.sess = tf.Session(config=config)
        self.saver = tf.train.Saver()
        self.saver.restore(self.sess, self.model_dir)

    @batching
    def encode(self, img: List['np.ndarray'], *args, **kwargs) -> np.ndarray:
        ret = []
        img = [(np.array(Image.fromarray(im).resize((self.inception_size_x,
                         self.inception_size_y)), dtype=np.float32) * 2 / 255. - 1.) for im in img]
        for _im in batch_iterator(img, self.batch_size):
            _, end_points_ = self.sess.run((self.logits, self.end_points),
                                           feed_dict={self.inputs: _im})
            ret.append(end_points_[self.select_layer])
        return np.concatenate(ret, axis=0).astype(np.float32)
