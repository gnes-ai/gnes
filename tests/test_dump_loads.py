import os
import unittest

import numpy as np

from src.nes.encoder.lopq import LOPQEncoder


class TestDumpAndLoad(unittest.TestCase):
    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'encoder.bin')
        self.test_vecs = np.random.random([1000, 100]).astype('float32')

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)

    def _test(self, backend):
        num_bytes = 10
        lopq = LOPQEncoder(num_bytes, pca_output_dim=20, pq_backend=backend)
        lopq.train(self.test_vecs)
        out = lopq.encode(self.test_vecs)
        lopq.dump(self.dump_path)
        self.assertTrue(os.path.exists(self.dump_path))
        lopq2 = LOPQEncoder.load(self.dump_path)
        out2 = lopq2.encode(self.test_vecs)
        self.assertEqual(out, out2)

    def test_dumpload_np(self):
        self._test('numpy')

    def test_dumpload_tf(self):
        self._test('tensorflow')
