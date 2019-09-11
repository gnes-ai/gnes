import os
import unittest

import numpy as np

from gnes.indexer.chunk.bindexer import BIndexer


@unittest.SkipTest
class TestBIndexer(unittest.TestCase):
    def setUp(self):
        self.toy_data = np.array([[1, 2, 1, 2],
                                  [2, 1, 3, 4],
                                  [1, 2, 1, 2],
                                  [2, 1, 4, 3],
                                  [2, 1, 3, 4],
                                  [23, 32, 21, 33],
                                  [123, 132, 1, 1]]).astype(np.uint8)
        self.toy_label = [(234, 0), (432, 0), (123, 1), (321, 0), (1, 0), (2, 0), (6, 0)]

        self.toy_query = np.array([[1, 2, 1, 2],
                                   [2, 1, 3, 4],
                                   [3, 2, 1, 2]]).astype(np.uint8)

        self.toy_exp = [[(234, 0, 1., 1,), (123, 1, 1., 1)], [(432, 0, 1., 1), (1, 0, 1., 1)],
                        [(234, 0, 1., 0.75), (123, 1, 1., 0.75)]]
        self.weights = [1.] * len(self.toy_label)

        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'test-indexer.bin')

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)

    def test_nsw_search(self):
        fd = BIndexer(self.toy_data.shape[1], data_path=self.dump_path + '_1')
        fd.add(self.toy_label, self.toy_data, self.weights)
        self.assertEqual(fd.num_doc, 7)
        self.assertEqual(fd.num_chunks, 7)
        self.assertEqual(fd.num_chunks_avg, 1)

        rs = fd.query(self.toy_query, 2, method='nsw', normalized_score=False)
        for i in range(len(rs)):
            rs[i] = sorted(rs[i], key=lambda x: (x[3], x[0]))
        fd.close()
        self.assertEqual(rs, self.toy_exp)

    def test_force_search(self):
        fd = BIndexer(self.toy_data.shape[1], data_path=self.dump_path + '_2')
        fd.add(self.toy_label, self.toy_data, self.weights)
        rs = fd.query(self.toy_query, 2, method='force', normalized_score=False)
        for i in range(len(rs)):
            rs[i] = sorted(rs[i], key=lambda x: (x[3], x[0]))
        fd.close()
        self.assertEqual(rs, self.toy_exp)

    def test_dump_load(self):
        fd = BIndexer(self.toy_data.shape[1], data_path=self.dump_path + '_3')
        fd.add(self.toy_label, self.toy_data, self.weights)
        fd.dump()
        fd.close()
        # shutil.rmtree(self.data_path + "_3")

        fd2 = BIndexer.load(fd.dump_full_path)
        rs = fd2.query(self.toy_query, 2, normalized_score=False)
        for i in range(len(rs)):
            rs[i] = sorted(rs[i], key=lambda x: (x[3], x[0]))
        fd2.close()

        self.assertEqual(rs, self.toy_exp)
        os.remove(self.dump_path + '_3')
