import ctypes
import os
import unittest

import numpy as np

from gnes.indexer import HnswIndexer


class TestHnswIndexer(unittest.TestCase):
    def setUp(self):
        self.n_bytes = 20
        self.n_lines = 1000
        self.top_k = 1
        self.query_num = 10
        self.test_ints = np.random.randint(
            0, 255, [self.n_lines, self.n_bytes]).astype(np.uint8)

        self.test_bytes = self.test_ints.tobytes()

        self.test_docids = [np.random.randint(0, ctypes.c_uint(-1).value)
                            for _ in range(self.n_lines)]

        self.query_bytes = self.test_ints[:self.query_num].tobytes()
        self.query_result = []

        for i in range(self.query_num):
            rk = np.sum(np.minimum(np.abs(
                self.test_ints - self.test_ints[i]), 1), -1)
            rk = sorted(enumerate(rk), key=lambda x: x[1])[:self.top_k]
            self.query_result.append([(self.test_docids[k], r / self.n_bytes)
                                      for k, r in rk])

        self.db_path = './test_leveldb'
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'indexer.bin')

    def test_add(self):
        hnsw = HnswIndexer(num_bytes=self.n_bytes)
        hnsw.add(self.test_bytes, self.test_docids)
        self.assertEqual(self.n_bytes, hnsw.num_bytes)
        self.assertEqual(self.n_lines, hnsw.size)

    def test_query(self):
        hnsw = HnswIndexer(num_bytes=self.n_bytes)
        hnsw.add(self.test_bytes, self.test_docids)
        res = hnsw.query(self.query_bytes, self.top_k)
        print(res)

        rt = sum([self.query_result[i][j][0] == res[i][j][0]
                  for i in range(self.query_num)
                  for j in range(self.top_k)])
        rt2 = sum([self.query_result[i][j][1] == res[i][j][1]
                   for i in range(self.query_num)
                   for j in range(self.top_k)])

        self.assertEqual(rt, self.top_k * self.query_num)
        self.assertEqual(rt2, self.top_k * self.query_num)

    def dump_load(self):
        tmp = HnswIndexer(num_bytes=self.n_bytes)
        tmp.add(self.test_bytes, self.test_docids)
        tmp.dump(self.dump_path)

        hnsw = HnswIndexer.load(self.dump_path)
        res = hnsw.query(self.query_bytes, self.top_k)

        rt = sum([self.query_result[i][j][0] == res[i][j][0]
                  for i in range(self.query_num)
                  for j in range(self.top_k)])
        rt2 = sum([self.query_result[i][j][1] == res[i][j][1]
                   for i in range(self.query_num)
                   for j in range(self.top_k)])

        self.assertEqual(rt, self.top_k * self.query_num)
        self.assertEqual(rt2, self.top_k * self.query_num)
