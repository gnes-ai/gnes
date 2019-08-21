import os
import unittest

import numpy as np

from gnes.encoder.base import PipelineEncoder
from gnes.encoder.numeric.hash import HashEncoder


class TestHash(unittest.TestCase):
    def setUp(self):
        self.num_bytes = 16
        self.num_bits = 8
        self.num_idx = 2
        self.kmeans_clusters = 10
        self.x = 1000
        self.y = 128
        self.test_data = np.random.random([self.x, self.y]).astype(np.float32)
        dirname = os.path.dirname(__file__)
        self.hash_yaml = os.path.join(dirname, 'yaml', 'hash-encoder.yml')

    def test_train_pred(self):
        m = HashEncoder(self.num_bytes, self.num_bits,
                        self.num_idx, self.kmeans_clusters)
        m.train(self.test_data)
        self.assertEquals(self.num_idx, m.centroids.shape[1])
        self.assertEquals(self.kmeans_clusters, m.centroids.shape[2])
        self.assertEqual(self.y, m.centroids.shape[3])

        self.assertEqual(self.num_bytes, len(m.hash_cores))

        out = m.encode(self.test_data)
        self.assertEqual(self.x, out.shape[0])
        self.assertEqual(self.num_idx + self.num_bytes, out.shape[1])
        self.assertEqual(np.uint32, out.dtype)

    def test_yaml_load(self):
        pca_hash = PipelineEncoder.load_yaml(self.hash_yaml)
        pca_hash.train(self.test_data)
        out = pca_hash.encode(self.test_data)
        self.assertEqual(self.x, out.shape[0])
        self.assertEqual(self.num_idx + self.num_bytes, out.shape[1])
