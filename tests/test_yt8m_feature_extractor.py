import os
import unittest
import numpy as np

from gnes.encoder.base import BaseEncoder


class TestYT8MFeatureExtractor(unittest.TestCase):
    @unittest.skip
    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.test_img = [np.random.rand(10, 299, 299, 3).astype(np.uint8),
                         np.random.rand(6, 299, 299, 3).astype(np.uint8),
                         np.random.rand(8, 299, 299, 3).astype(np.uint8)]
        self.inception_yaml = os.path.join(dirname, 'yaml', 'yt8m_feature.yml')

    @unittest.skip
    def test_inception_encoding(self):
        self.encoder = BaseEncoder.load_yaml(self.inception_yaml)
        vec = self.encoder.encode(self.test_img)

        self.assertEqual(len(vec), len(self.test_img))
        self.assertEqual(len(vec[0].shape), 2)
        self.assertEqual(vec[0].shape[0], self.test_img[0].shape[0])
        self.assertEqual(vec[0].shape[1], 1152)
