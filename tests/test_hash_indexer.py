import os
import unittest

import numpy as np

from gnes.indexer.chunk.hbindexer import HBIndexer


class TestMHIndexer(unittest.TestCase):

    def setUp(self):
        self.num_clusters = 100
        self.num_bytes = 16
        self.n_idx = 1
        self.n = 100

        self.test_label = [(_, 1) for _ in range(self.n)]
        t = np.random.randint(0, 100, size=[self.n, self.n_idx + self.num_bytes])
        self.test_data = t.astype(np.uint32)
        self.weights = [1.] * len(self.test_label)
        self.data_path = 'test_path'
        self.dump_path = './dump.bin'

        self.query = self.test_data

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)

    def test_add_query(self):
        m = HBIndexer(self.num_clusters, self.num_bytes, self.n_idx, self.data_path)
        m.add(self.test_label, self.test_data, self.weights)
        res = m.query(self.query, 1)
        self.assertEqual(len(res), self.n)
        s = sum([1 for i in range(self.n) if i in [_[0][0] for _ in res[i]]])
        self.assertEqual(s, self.n)
        m.close()

    def test_dump_load(self):
        m = HBIndexer(self.num_clusters, self.num_bytes, self.n_idx, self.data_path)
        m.add(self.test_label, self.test_data, self.weights)
        m.dump(self.dump_path)
        m.close()
        self.assertTrue(os.path.exists(self.dump_path))
        m2 = HBIndexer.load(self.dump_path)
        res = m2.query(self.query, 1)
        s = sum([1 for i in range(self.n) if i in [_[0][0] for _ in res[i]]])
        self.assertEqual(s, self.n)
