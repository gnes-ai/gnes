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
from ..base import BaseVideoEncoder
from ...helper import batching, get_first_available_gpu


class YouTube8MEncoder(BaseVideoEncoder):
    batch_size = 64

    def __init__(self, model_dir: str,
                 model_name: str,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model_dir = model_dir
        self.model_name = model_name
        self.max_num_frames = 300
        self.embedding_dim = 1152

    def post_init(self):
        import tensorflow as tf
        import os
        os.environ['CUDA_VISIBLE_DEVICES'] = str(get_first_available_gpu())

        g = tf.Graph()
        with g.as_default():
            checkpoint_file = os.path.join(self.model_dir, self.model_name,
                                           "inference_model")
            meta_graph_location = checkpoint_file + ".meta"
            saver = tf.train.import_meta_graph(meta_graph_location, clear_devices=True)

            config = tf.ConfigProto(log_device_placement=False)
            if self.on_gpu:
                config.gpu_options.allow_growth = True
            self.sess = tf.Session(config=config)
            saver.restore(self.sess, checkpoint_file)

            self.input_tensor = tf.get_collection("input_batch_raw")[0]
            self.num_frames_tensor = tf.get_collection("num_frames")[0]
            self.predictions_tensor = self.sess.graph.get_tensor_by_name("tower/gates/MatMul:0")

    def encode(self, data: List['np.ndarray'], *args, **kwargs) -> np.ndarray:
        def _padding(data):
            _data = np.array([np.concatenate((d, np.zeros((self.max_num_frames - d.shape[0], self.embedding_dim), dtype=np.float32)),
                            axis=0) if d.shape[0] < self.max_num_frames else d[:self.max_num_frames] for d in data])
            return _data.reshape((-1, self.max_num_frames, self.embedding_dim))

        @batching
        def _encode(_, data):
            num_frames_list = list(map(lambda x: x.shape[0], data))
            predictions_val, = self.sess.run([self.predictions_tensor],
                        feed_dict={self.input_tensor: _padding(data),
                                   self.num_frames_tensor: np.array(num_frames_list)})
            return np.array(predictions_val).astype(np.float32)

        return _encode(self, _padding(data))


