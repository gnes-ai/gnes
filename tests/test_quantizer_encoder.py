import os
import unittest
import numpy as np

from gnes.encoder.base import BaseNumericEncoder


class TestQuantizerEncoder(unittest.TestCase):
    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.vanilla_quantizer_yaml = os.path.join(dirname, 'yaml', 'quantizer_encoder.yml')

    def test_vanilla_quantizer(self):
        encoder = BaseNumericEncoder.load_yaml(self.vanilla_quantizer_yaml)
        encoder.train()

        vecs_1 = np.random.uniform(-150, 150, size=[1000, 160]).astype('float32')
        out = encoder.encode(vecs_1)
        self.assertEqual(len(out.shape), 2)
        self.assertEqual(out.shape[0], 1000)
        self.assertEqual(out.shape[1], 16)

        vecs_2 = np.random.uniform(-1, 1, size=[1000, 160]).astype('float32')
        self.assertRaises(Warning, encoder.encode, vecs_2)

        vecs_3 = np.random.uniform(-1, 1000, size=[1000, 160]).astype('float32')
        self.assertRaises(Warning, encoder.encode, vecs_3)

