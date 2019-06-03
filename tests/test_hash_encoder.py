import os
import unittest

import numpy as np
from gnes.encoder.hash import HashEncoder


class TestHash(unittest.TestCase):
    def setUp(self):
        self.num_bytes = 16
        self.num_bits = 8
        self.num_idx = 2
        self.kmeans_clusters = 10
        self.x = 1000
        self.y = 128
        self.test_data = np.random.random([self.x, self.y]).astype(np.float32)
        self.test_data2 = np.random.random([1, self.y+1]).astype(np.float32)
        self.test_data3 = np.random.random([self.x, self.y+1]).astype(np.float32)

    def test_train_pred(self):
        m = HashEncoder(self.num_bytes, self.num_bits,
                        self.num_idx, self.kmeans_clusters)
        m.train(self.test_data)
        self.assertEquals(2, len(m.centroids))
        self.assertEquals((self.kmeans_clusters, self.y), m.centroids[0].shape)
        self.assertEqual(self.num_idx, len(m.hash_cores))

        out = m.encode(self.test_data)
        self.assertEqual(self.x, out.shape[0])
        self.assertEqual(self.num_idx+self.num_bytes, out.shape[1])
        self.assertEqual(np.uint32, out.dtype)

    def test_exception(self):
        m = HashEncoder(self.num_bytes, self.num_bits,
                        self.num_idx, self.kmeans_clusters)
        self.assertRaises(ValueError, m.train(self.test_data3))

        m.train(self.test_data)
        self.assertRaises(ValueError, m.encode(self.test_data2))
