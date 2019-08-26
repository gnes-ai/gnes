import unittest

import numpy as np
import torch
from numpy.testing import assert_allclose

from gnes.encoder.numeric.pooling import PoolingEncoder


class TestEncoder(unittest.TestCase):
    def setUp(self):
        self.seq_data = np.random.random([5, 10])
        self.seq_embed_data = np.random.random([5, 10, 32])
        self.mask_data = np.array(self.seq_data > 0.5, np.float32)
        self.data = [
            (torch.tensor(self.seq_embed_data, dtype=torch.float32), torch.tensor(self.mask_data, dtype=torch.float32)),
            (self.seq_embed_data, self.mask_data),
            (self.seq_embed_data, self.mask_data)]

    def _test_strategy(self, strategy):
        pe_to = PoolingEncoder(strategy, 'torch')
        pe_tf = PoolingEncoder(strategy, 'tensorflow')
        pe_np = PoolingEncoder(strategy, 'numpy')
        return [pe.encode(self.data[idx]) for idx, pe in enumerate([pe_to, pe_tf, pe_np])]

    def test_all(self):
        for s in {'REDUCE_MEAN', 'REDUCE_MAX', 'REDUCE_MEAN_MAX'}:
            with self.subTest(strategy=s):
                r = self._test_strategy(s)
                for rr in r:
                    print(type(rr))
                    print(rr)
                    print('---')
                assert_allclose(r[0], r[1], rtol=1e-5)
                assert_allclose(r[1], r[2], rtol=1e-5)
