import os

import GPUtil
import numpy as np
import tensorflow as tf

from . import BaseEncoder as BE
from .pq import PQEncoder

DEVICE_ID_LIST = GPUtil.getAvailable(order='random',
                                     maxMemory=0.1,
                                     maxLoad=0.1,
                                     limit=1)
if DEVICE_ID_LIST:
    os.environ['CUDA_VISIBLE_DEVICES'] = str(DEVICE_ID_LIST[0])


class TFPQEncoder(PQEncoder):
    def __init__(self, k: int, m: int, num_clusters: int = 50):
        super().__init__(k, m, num_clusters)
        self._build_graph()
        self._sess = tf.Session()
        self._sess.run(tf.global_variables_initializer())

    def _build_graph(self):
        self.ph_centroids = tf.placeholder(tf.float32,
                                           [1, self.num_bytes,
                                            self.num_clusters,
                                            self.m])
        ph_centroids = tf.squeeze(self.ph_centroids, 0)
        self.ph_x = tf.placeholder(tf.float32, [None, self.num_bytes, self.m])
        # [self.num_bytes, None, self.m]
        self.x = tf.transpose(self.ph_x, [1, 0, 2])
        ty = tf.reduce_sum(tf.square(ph_centroids), axis=2, keepdims=True)
        ty = tf.transpose(ty, [0, 2, 1])
        tx = tf.reduce_sum(tf.square(self.x), axis=2, keepdims=True)
        diff = tf.matmul(self.x, tf.transpose(ph_centroids, [0, 2, 1]))
        diff = tx + ty - 2 * diff
        # start from 1
        self.p = tf.argmax(-diff, axis=2) + 1
        self.p = tf.transpose(self.p, [1, 0])

    @BE.train_required
    def encode(self, vecs, batch_size: int = 10000) -> bytes:
        num_points = vecs.shape[0]
        vecs = np.reshape(vecs, [num_points, self.num_bytes, self.m])
        i = 0
        res = []
        while batch_size * i < vecs.shape[0]:
            m = batch_size * i
            n = batch_size * (i + 1)
            tmp = self._sess.run(self.p,
                                 feed_dict={self.ph_x: vecs[m:n],
                                            self.ph_centroids: self.centroids})
            res.append(tmp)
            i += 1
        return np.concatenate(res, 0).astype(np.uint8).tobytes()
