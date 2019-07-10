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
import tensorflow as tf
from gnes.helper import batch_iterator
from ..base import BaseImageEncoder


class TFInceptionEncoder(BaseImageEncoder):

    def __init__(self, model_dir: str,
                 batch_size: int = 64,
                 image_height: int = 299,
                 image_width: int = 299,
                 select_layer: str = 'PreLogitsFlatten',
                 use_gpu: bool = True,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model_dir = model_dir
        self.batch_size = batch_size
        self.image_height = image_height
        self.image_width = image_width
        self.select_layer = select_layer
        self.use_gpu = use_gpu

    def post_init(self):
        from .inception_v4.inception_v4 import inception_v4, inception_utils
        arg_scope = inception_utils.inception_arg_scope()
        self.inputs = tf.placeholder(tf.float32, (None,
                                                  self.image_height,
                                                  self.image_width,
                                                  3))
        slim = tf.contrib.slim
        with slim.arg_scope(arg_scope):
            self.logits, self.end_points = inception_v4(self.inputs,
                                                        is_training=False,
                                                        dropout_keep_prob=1.0)

        config = tf.ConfigProto(log_device_placement=True)
        if self.use_gpu:
            config.gpu_options.allow_growth = True
        self.sess = tf.Session(config=config)
        self.saver = tf.train.Saver()
        self.saver.restore(self.sess, self.model_dir)

    def encode(self, img: List['np.ndarray'], *args, **kwargs) -> np.ndarray:
        ret = []
        for _im in batch_iterator(img, self.batch_size):
            _, end_points_ = self.sess.run((self.logits, self.end_points),
                                           feed_dict={self.inputs: _im})
            ret.append(end_points_[self.select_layer])
        return np.concatenate(ret, axis=0).astype(np.float32)
