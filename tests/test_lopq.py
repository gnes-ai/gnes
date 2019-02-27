import os
import unittest

import numpy as np

from src.nes.encoder.lopq import LOPQEncoder


class TestPCA(unittest.TestCase):
    def setUp(self):
        self.k = 40
        self.m = 5
        self.num_clusters = 100
        self.input_dim = 120
        self.test_vecs = np.random.random([1000, self.input_dim])
        self.test_vecs = np.array(self.test_vecs, np.float32)
        self.test_params_path = './params.pkl'

    def tearDown(self):
        if os.path.exists(self.test_params_path):
            os.remove(self.test_params_path)
        return

    def test_train(self):
        lopq = LOPQEncoder(self.k, self.m, self.num_clusters)
        lopq.train(self.test_vecs)

    def test_encode(self):
        lopq = LOPQEncoder(self.k, self.m, self.num_clusters)
        lopq.train(self.test_vecs)
        out = lopq.encode(self.test_vecs)
        self.assertEqual(bytes, type(out))
        self.assertEqual(self.test_vecs.shape[0]*int(self.k / self.m),
                         len(out))

    def test_encode_single(self):
        lopq = LOPQEncoder(self.k, self.m, self.num_clusters)
        lopq.train(self.test_vecs)
        out = lopq.encode_single(self.test_vecs[:10])
        self.assertEqual(10*int(self.k / self.m), len(out))
        self.assertEqual(bytes, type(out))


if __name__ == '__main__':
    unittest.main()
