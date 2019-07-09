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

# pylint: disable=low-comment-ratio


from typing import Dict, Any

import numpy as np

from .pq import PQEncoder
from ...helper import batching, train_required, get_first_available_gpu


class TFPQEncoder(PQEncoder):
    @classmethod
    def pre_init(cls):
        import os
        os.environ['CUDA_VISIBLE_DEVICES'] = str(get_first_available_gpu())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch_size = 8192

    def post_init(self):
        import tensorflow as tf
        self._graph = self._get_graph()
        self._sess = tf.Session()
        self._sess.run(tf.global_variables_initializer())

    def _get_graph(self) -> Dict[str, Any]:
        import tensorflow as tf
        ph_x = tf.placeholder(tf.float32, [None, self.num_bytes, None])
        ph_centroids = tf.placeholder(tf.float32, [1, self.num_bytes, self.num_clusters, None])
        centroids_squeezed = tf.squeeze(ph_centroids, 0)
        # [self.num_bytes, None, self.m]
        x = tf.transpose(ph_x, [1, 0, 2])
        ty = tf.reduce_sum(tf.square(centroids_squeezed), axis=2, keepdims=True)
        ty = tf.transpose(ty, [0, 2, 1])
        tx = tf.reduce_sum(tf.square(x), axis=2, keepdims=True)
        diff = tf.matmul(x, tf.transpose(centroids_squeezed, [0, 2, 1]))
        diff = tx + ty - 2 * diff
        # start from 1
        p = tf.argmax(-diff, axis=2) + 1
        p = tf.transpose(p, [1, 0])
        return {
            'out': p,
            'ph_x': ph_x,
            'ph_centroids': ph_centroids
        }

    @train_required
    @batching
    def encode(self, vecs: np.ndarray, *args, **kwargs) -> np.ndarray:
        vecs = np.reshape(vecs, [vecs.shape[0], self.num_bytes, -1])
        tmp = self._sess.run(self._graph['out'],
                             feed_dict={self._graph['ph_x']: vecs,
                                        self._graph['ph_centroids']: self.centroids})
        return tmp.astype(np.uint8)


    def close(self):
        self._sess.close()
