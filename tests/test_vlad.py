import os
import unittest
import numpy as np
from gnes.encoder.numeric.vlad import VladEncoder


class TestVladEncoder(unittest.TestCase):
    def setUp(self):
        self.mock_train_data = np.random.random([1, 200, 128]).astype(np.float32)
        self.mock_eval_data = np.random.random([2, 2, 128]).astype(np.float32)
        self.dump_path = os.path.join(os.path.dirname(__file__), 'vlad.bin')

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)

    def test_vlad_train(self):
        model = VladEncoder(20)
        model.train(self.mock_train_data)
        self.assertEqual(model.centroids.shape, (20, 128))
        v = model.encode(self.mock_eval_data)
        self.assertEqual(v.shape, (2, 2560))

    def test_vlad_dump_load(self):
        model = VladEncoder(20)
        model.train(self.mock_train_data)
        model.dump(self.dump_path)
        model_new = VladEncoder.load(self.dump_path)
        self.assertEqual(model_new.centroids.shape, (20, 128))
