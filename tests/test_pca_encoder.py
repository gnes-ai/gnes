import os
import unittest
import numpy as np

from gnes.encoder.base import BaseEncoder


class TestPCAEncoder(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'pca_encoder.bin')
        self.yaml_path = os.path.join(dirname, 'yaml', 'pca.yml')
        self.test_numeric = np.random.randint(0, 255, (1000, 1024)).astype('float32')

    def test_encoding(self):
        self.encoder = BaseEncoder.load_yaml(self.yaml_path)
        # train before encode to create pca_components
        self.encoder.train(self.test_numeric)
        vec = self.encoder.encode(self.test_numeric)
        self.assertEqual(vec.shape, (1000, 300))
        # dump after train with valied pca_components
        self.encoder.dump(self.dump_path)
        encoder2 = BaseEncoder.load(self.dump_path)
        vec = encoder2.encode(self.test_numeric)
        self.assertEqual(vec.shape, (1000, 300))

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)
