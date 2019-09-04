import os
import unittest
import numpy as np

from gnes.encoder.base import BaseEncoder


class TestYT8MFeatureExtractor(unittest.TestCase):

    @unittest.skip
    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.test_img = [np.random.rand(299, 299, 3).astype(np.uint8),
                         np.random.rand(299, 299, 3).astype(np.uint8)]
        self.inception_yaml = os.path.join(dirname, 'yaml', 'yt8m_feature.yml')

    @unittest.skip
    def test_inception_encoding(self):
        self.encoder = BaseEncoder.load_yaml(self.inception_yaml)
        # for test_img in self.test_img:
        vec = self.encoder.encode(self.test_img)
        print("the length of data now is:", len(self.test_img))
        print("after encoding", vec.shape)

        self.assertEqual(vec.shape[0], len(self.test_img))
        self.assertEqual(vec.shape[1], 1024)
