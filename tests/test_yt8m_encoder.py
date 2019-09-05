import os
import unittest
import numpy as np

from gnes.encoder.base import BaseEncoder


class TestYT8MEncoder(unittest.TestCase):
    @unittest.skip
    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.test_video = [np.random.rand(10, 1152).astype(np.uint8),
                         np.random.rand(15, 1152).astype(np.uint8),
                         np.random.rand(20, 1152).astype(np.uint8)]
        self.yt8m_yaml = os.path.join(dirname, 'yaml', 'yt8m_encoder.yml')

    @unittest.skip
    def test_yt8m_encoding(self):
        self.encoder = BaseEncoder.load_yaml(self.yt8m_yaml)
        vec = self.encoder.encode(self.test_video)

        self.assertEqual(vec.shape[0], len(self.test_video))
        self.assertEqual(vec.shape[1], 19310)