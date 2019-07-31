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
from PIL import Image

from ..base import BaseVideoEncoder
from ...helper import batching, batch_iterator, get_first_available_gpu


class IncepMixtureEncoder(BaseVideoEncoder):

    def __init__(self, model_dir_inception: str,
                 model_dir_mixture: str,
                 batch_size: int = 64,
                 select_layer: str = 'PreLogitsFlatten',
                 use_cuda: bool = False,
                 feature_size: int = 300,
                 vocab_size: int = 28,
                 cluster_size: int = 256,
                 method: str = 'netvlad',
                 input_size: int = 1536,
                 multitask_method: str = 'Attention'
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_dir_inception = model_dir_inception
        self.model_dir_mixture = model_dir_mixture
        self.batch_size = batch_size
        self.select_layer = select_layer
        self.use_cuda = use_cuda
        self.cluster_size = cluster_size
        self.feature_size = feature_size
        self.vocab_size = vocab_size
        self.method = method
        self.input_size = input_size
        self.multitask_method = multitask_method

    def post_init(self):
        import tensorflow as tf
        from ..image.inception_cores.inception_v4 import inception_v4
        from ..image.inception_cores.inception_utils import inception_arg_scope
        from .mixture_core.incep_mixture import *
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
            if self._use_cuda:
                config.gpu_options.allow_growth = True
            self.sess = tf.Session(config=config)
            self.saver = tf.train.Saver()
            self.saver.restore(self.sess, self.model_dir_inception)

        g2 = tf.Graph()
        with g2.as_default():
            config = tf.ConfigProto(log_device_placement=False)
            if self._use_cuda:
                config.gpu_options.allow_growth = True
            self.sess2 = tf.Session(config=config)
            self.mix_model = NetFV(feature_size=self.feature_size,
                                   cluster_size=self.cluster_size,
                                   vocab_size=self.vocab_size,
                                   input_size=self.input_size,
                                   use_2nd_label=True,
                                   multitask_method=self.multitask_method,
                                   method=self.method,
                                   is_training=False)
            saver = tf.train.Saver(max_to_keep=1)
            self.sess2.run(tf.global_variables_initializer())
            saver.restore(self.sess2, self.model_dir_mixture)
