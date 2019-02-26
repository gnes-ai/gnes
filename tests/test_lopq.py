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
        self.test_pred_path = './test.pred.bin'

    def tearDown(self):
        if os.path.exists(self.test_params_path):
            os.remove(self.test_params_path)
        if os.path.exists(self.test_pred_path):
            os.remove(self.test_pred_path)
        return

    def test_train(self):
        lopq = LOPQEncoder(self.k, self.m, self.num_clusters)
        lopq.train(self.test_vecs)
        self.assertTrue(os.path.exists(self.test_params_path))
        self.assertTrue(os.path.exists(self.test_pred_path))

    def test_transbatch(self):
        lopq = LOPQEncoder(self.k, self.m, self.num_clusters)
        lopq.train(self.test_vecs)
        out = lopq.encode(self.test_vecs)
        self.assertEqual(self.test_vecs.shape[0], out.shape[0])
        self.assertEqual(int(self.k / self.m), out.shape[1])
        self.assertEqual(np.uint8, out.dtype)

    def test_transsingle(self):
        lopq = LOPQEncoder(self.k, self.m, self.num_clusters)
        lopq.train(self.test_vecs)
        for i in range(10):
            out = lopq.encode_single(self.test_vecs[i:i + 1])
            print(out.shape)
        self.assertEqual(int(self.k / self.m), out.shape[1])


if __name__ == '__main__':
    unittest.main()
