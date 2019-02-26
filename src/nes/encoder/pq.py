import os
from typing import List

import GPUtil
import faiss
import numpy as np
import tensorflow as tf

DEVICE_ID_LIST = GPUtil.getAvailable(order='random',
                                     maxMemory=0.1,
                                     maxLoad=0.1,
                                     limit=1)
if DEVICE_ID_LIST:
    os.environ['CUDA_VISIBLE_DEVICES'] = str(DEVICE_ID_LIST[0])


def train_kmeans(x: np.ndarray, num_clusters: int, num_iter: int = 20) -> np.ndarray:
    kmeans = faiss.Kmeans(x.shape[1],
                          num_clusters,
                          num_iter,
                          True)
    kmeans.train(x)

    return kmeans.centroids


class PQ:
    def __init__(self, k: int, m: int, num_clusters: int = 50):
        self.k = k
        self.m = m
        self.num_bytes = int(k / m)
        self.num_clusters = num_clusters
        self.centroids = []  # type: List[np.ndarray]
        self.build_graph()

    def build_graph(self):
        self.ph_centroids = tf.placeholder(tf.float32,
                                           [self.num_bytes,
                                            self.num_clusters,
                                            self.m])
        self.ph_x = tf.placeholder(tf.float32, [None, self.num_bytes, self.m])
        # [self.num_bytes, None, self.m]
        self.x = tf.transpose(self.ph_x, [1, 0, 2])
        ty = tf.reduce_sum(tf.square(self.ph_centroids), axis=2,
                           keepdims=True)
        ty = tf.transpose(ty, [0, 2, 1])
        tx = tf.reduce_sum(tf.square(self.x), axis=2, keepdims=True)
        diff = tf.matmul(self.x, tf.transpose(self.ph_centroids, [0, 2, 1]))
        diff = tx + ty - 2 * diff
        # start from 1
        self.p = tf.argmax(-diff, axis=2) + 1
        self.p = tf.transpose(self.p, [1, 0])

    def fit(self, csv: np.ndarray, save_path: str = None, pred_path: str = None):
        assert csv.shape[1] == self.k, 'Incorrect dimension for input!'

        for j in range(self.num_bytes):
            store = csv[:, self.m * j:self.m * (j + 1)]
            store = np.array(store, dtype=np.float32)
            self.centroids.append(train_kmeans(
                store,
                num_clusters=self.num_clusters))

        self.centroids = np.array(self.centroids, dtype=np.float32)
        if save_path:
            self.save(save_path=save_path)
        if pred_path:
            self.transform_batch(csv, data_path=pred_path)

    def transform_batch(self, vecs, batch_size=10000, data_path=None) -> np.ndarray:
        num_points = vecs.shape[0]
        vecs = np.reshape(vecs, [num_points, self.num_bytes, self.m])
        i = 0
        res = []
        with tf.Session() as sess:
            sess.run(tf.global_variables_initializer())
            while batch_size * i < vecs.shape[0]:
                m = batch_size * i
                n = batch_size * (i + 1)
                tmp = sess.run(self.p,
                               feed_dict={self.ph_x: vecs[m:n],
                                          self.ph_centroids: self.centroids})
                res.append(tmp)
                i += 1
        res = np.concatenate(np.array(res, dtype=np.uint8), 0)

        if data_path:
            with open(data_path, 'ab') as f:
                f.write(res.tobytes())
        else:
            return res

    def transform_single(self, vecs: np.ndarray) -> np.ndarray:
        x = np.reshape(vecs, [self.num_bytes, 1, self.m])
        x = np.sum(np.square(x - self.centroids), -1)
        x = np.argmax(-x, 1)

        return np.array(x, dtype=np.uint8)
