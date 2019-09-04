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

from ..base import BaseImageEncoder
from ...helper import batching, get_first_available_gpu


class TFInceptionEncoder(BaseImageEncoder):
    batch_size = 64

    def __init__(self, model_dir: str,
                 select_layer: str = 'PreLogitsFlatten',
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model_dir = model_dir
        self.select_layer = select_layer
        self.inception_size_x = 299
        self.inception_size_y = 299

    def post_init(self):
        import tensorflow as tf
        from .inception_cores.inception_v4 import inception_v4
        from .inception_cores.inception_utils import inception_arg_scope
        import os
        os.environ['CUDA_VISIBLE_DEVICES'] = str(get_first_available_gpu())
        g = tf.Graph()
        with g.as_default():
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
            if self.on_gpu:
                config.gpu_options.allow_growth = True
            self.sess = tf.Session(config=config)
            self.saver = tf.train.Saver()
            self.saver.restore(self.sess, self.model_dir)

    def encode(self, img: List['np.ndarray'], *args, **kwargs) -> np.ndarray:
        img = [(im * 2 / 255. - 1.) for im in img]

        @batching
        def _encode(_, data):
            _, end_points_ = self.sess.run((self.logits, self.end_points),
                                           feed_dict={self.inputs: data})
            return end_points_[self.select_layer]

        return _encode(self, img).astype(np.float32)
