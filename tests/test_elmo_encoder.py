import os
import unittest
from shutil import rmtree

import numpy as np

from gnes.encoder.base import PipelineEncoder
from gnes.encoder.elmo import ElmoEncoder
from gnes.module.gnes import GNES
from gnes.proto import gnes_pb2


class TestElmoEncoder(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'elmo_encoder.bin')
        self.ebe_path = os.path.join(dirname, 'yaml', 'elmo-binary-encoder.yml')

        self.test_str = []
        with open(os.path.join(dirname, 'tangshi.txt')) as f:
            for line in f:
                line = line.strip()
                if line:
                    self.test_str.append(line)

    def test_encoding(self):
        elmo_encoder = ElmoEncoder(
            model_dir=os.environ.get('ELMO_CI_MODEL', '/zhs.model'),
            pooling_strategy="REDUCE_MEAN")
        vec = elmo_encoder.encode(self.test_str)
        self.assertEqual(vec.shape[0], len(self.test_str))
        self.assertEqual(vec.shape[1], 1024)

        num_bytes = 8

        ebe = PipelineEncoder.load_yaml(self.ebe_path)
        self.assertRaises(RuntimeError, ebe.encode, self.test_str)

        ebe.train(self.test_str)
        out = ebe.encode(self.test_str)
        ebe.close()
        self.assertEqual(np.ndarray, type(out))
        self.assertEqual(num_bytes, out.shape[1])
        self.assertEqual(len(self.test_str), len(out))

        ebe.dump(self.dump_path)
        self.assertTrue(os.path.exists(self.dump_path))
        ebe2 = PipelineEncoder.load(self.dump_path)
        out2 = ebe2.encode(self.test_str)
        # TODO: fix this
        # self.assertEqual(out, out2)


    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)
