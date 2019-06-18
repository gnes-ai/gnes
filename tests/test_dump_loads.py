import os
import unittest

import numpy as np

from gnes.encoder.base import PipelineEncoder


class TestDumpAndLoad(unittest.TestCase):
    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.lopq_yaml_np = os.path.join(dirname, 'yaml', 'lopq-encoder-2-np.yml')
        self.dump_path = os.path.join(dirname, 'encoder.bin')
        self.test_vecs = np.random.random([1000, 100]).astype('float32')

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)

    def _test(self, yaml_fp):
        lopq = PipelineEncoder.load_yaml(yaml_fp)
        lopq.train(self.test_vecs)
        out = lopq.encode(self.test_vecs)
        lopq.dump(self.dump_path)
        self.assertTrue(os.path.exists(self.dump_path))
        lopq2 = PipelineEncoder.load(self.dump_path)
        out2 = lopq2.encode(self.test_vecs)
        self.assertEqual(out, out2)

    def test_dumpload_np(self):
        self._test(self.lopq_yaml_np)
