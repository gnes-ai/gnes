import os
import unittest
from shutil import rmtree

import numpy as np

from src.nes.encoder.lopq import LOPQEncoder


class TestDumpAndLoad(unittest.TestCase):
    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'encoder.bin')
        self.test_vecs = np.random.random([1000, 100])

    def test_dumpload_np(self):
        def _test(backend):
            num_bytes = 10
            lopq = LOPQEncoder(num_bytes, backend=backend)
            lopq.train(self.test_vecs)
            out = lopq.encode(self.test_vecs)
            lopq.dump(self.dump_path)
            self.assertTrue(os.path.exists(self.dump_path))
            lopq2 = LOPQEncoder.load(self.dump_path)
            out2 = lopq2.encode(self.test_vecs)
            self.assertEqual(out, out2)

        _test('numpy')
        _test('tensorflow')

    def tearDown(self):
        if os.path.exists(self.dump_path):
            rmtree(self.dump_path)
