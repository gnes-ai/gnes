import os
import unittest

from gnes.encoder.base import BaseEncoder


class TestTorchTransformersEncoder(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'model.bin')
        self.text_yaml = os.path.join(dirname, 'yaml', 'torch-transformers-encoder.yml')
        self.tt_encoder = BaseEncoder.load_yaml(self.text_yaml)

        self.test_str = []
        with open(os.path.join(dirname, 'sonnets_small.txt')) as f:
            for line in f:
                line = line.strip()
                if line:
                    self.test_str.append(line)

    def test_encoding(self):
        vec = self.tt_encoder.encode(self.test_str)
        self.assertEqual(vec.shape[0], len(self.test_str))
        self.assertEqual(vec.shape[1], 768)

    def test_dump_load(self):
        self.tt_encoder.dump(self.dump_path)

        tt_encoder2 = BaseEncoder.load(self.dump_path)

        vec = tt_encoder2.encode(self.test_str)
        self.assertEqual(vec.shape[0], len(self.test_str))
        self.assertEqual(vec.shape[1], 768)

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)
