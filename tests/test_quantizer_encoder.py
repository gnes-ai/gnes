import os
import unittest
import numpy as np

from gnes.encoder.base import BaseNumericEncoder


class TestQuantizerEncoder(unittest.TestCase):
    def setUp(self):
        self.vecs = np.random.randint(-150, 150, size=[1000, 160]).astype('float32')
        dirname = os.path.dirname(__file__)
        self.vanilla_quantizer_yaml = os.path.join(dirname, 'yaml', 'quantizer_encoder.yml')

    def test_vanilla_quantizer(self):
        encoder = BaseNumericEncoder.load_yaml(self.vanilla_quantizer_yaml)
        encoder.train()
        out = encoder.encode(self.vecs)
        print(out.shape)

