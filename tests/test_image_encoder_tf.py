import os
import numpy as np
from gnes.encoder.image.inception import TFInceptionEncoder
import unittest


class TestTFImageEncoder(unittest.TestCase):
    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.yaml_path = os.path.join(dirname, 'yaml', 'tf-inception-encoder.yaml')
        self.test_data_1 = [np.random.uniform(0, 1, size=(299, 299, 3)).astype(np.uint8) for _ in range(1)]
        self.test_data_2 = [np.random.uniform(0, 1, size=(299, 299, 3)).astype(np.uint8) for _ in range(100)]

    def test_encoding(self):
        self.encoder = TFInceptionEncoder.load_yaml(self.yaml_path)
        ret1 = self.encoder.encode(self.test_data_1)
        ret2 = self.encoder.encode(self.test_data_2)
        self.assertEqual(ret1.shape[0], 1)
        self.assertEqual(ret2.shape[0], 1000)
