import os
import unittest

import numpy as np

from gnes.helper import batch_iterator, TimeContext
from gnes.indexer.chunk.helper import DictKeyIndexer, NumpyKeyIndexer, ListKeyIndexer, ListNumpyKeyIndexer


class TestProto(unittest.TestCase):
    def setUp(self):
        self.num_sample = 1000000
        self.num_query = 10000
        self.keys = np.array([j for j in range(self.num_sample)])
        self.key_offset = np.stack([self.keys, np.random.randint(0, 255, size=[self.num_sample])],
                                   axis=1).tolist()
        self.weights = np.random.random(size=[self.num_sample]).tolist()
        self.query = np.random.randint(0, self.num_sample, size=[self.num_query]).tolist()
        self.dump_path = './dump.bin'

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)

    def _test_any(self, cls):
        a = cls()
        self.assertEqual(a.num_chunks, 0)
        a.add(self.key_offset, self.weights)
        self.assertEqual(a.num_chunks, self.num_sample)

        res1 = a.query(self.query)
        res2 = [(*self.key_offset[q], self.weights[q]) for q in self.query]
        self.assertListEqual(res1, res2)

        # test dump and reload
        a.dump(self.dump_path)
        b = cls.load(self.dump_path)
        res1 = a.query(self.query)
        res2 = b.query(self.query)
        self.assertListEqual(res1, res2)

    def test_numpy(self):
        self._test_any(NumpyKeyIndexer)

    def test_list(self):
        self._test_any(ListKeyIndexer)

    def test_fast_list(self):
        self._test_any(ListNumpyKeyIndexer)

    def test_dict(self):
        self._test_any(DictKeyIndexer)

    def test_bench_numpy_list(self):
        for cls in [ListKeyIndexer, NumpyKeyIndexer, ListNumpyKeyIndexer, DictKeyIndexer]:
            a = cls()
            b_size = 1000
            with TimeContext('%s:add()' % cls.__name__):
                for k, w in zip(batch_iterator(self.key_offset, b_size), batch_iterator(self.weights, b_size)):
                    a.add(k, w)
                self.assertEqual(a.num_docs, self.num_sample)
                self.assertEqual(a.num_chunks, self.num_sample)

            with TimeContext('%s:query()' % cls.__name__):
                for k in batch_iterator(self.query, b_size):
                    a.query(k)
