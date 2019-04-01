import os
import unittest

import numpy as np

from gnes.indexer import BIndexer


class TestFIndexer(unittest.TestCase):
    def setUp(self):
        self.toy_data = np.array([[1, 2, 1, 2],
                                  [2, 1, 3, 4],
                                  [1, 2, 1, 2],
                                  [2, 1, 4, 3],
                                  [2, 1, 3, 4],
                                  [23, 32, 21, 33],
                                  [123, 132, 1, 1]]).astype(np.uint8)
        self.toy_label = [234, 432, 123, 321, 1, 2, 6]

        self.toy_query = np.array([[1, 2, 1, 2],
                                   [2, 1, 3, 4],
                                   [3, 2, 2, 1]]).astype(np.uint8)

        self.toy_exp = [[234, 123], [432, 1], []]

        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'indexer.bin')

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)

    def test_db(self):
        fd = BIndexer(self.toy_data.shape[1])
        fd.add(self.toy_label, self.toy_data.tobytes())
        rs = fd.query(self.toy_query.tobytes())
        self.assertEqual(self.toy_data.shape, fd._vectors.shape)
        self.assertEqual(len(self.toy_label), len(fd._doc_ids))
        self.assertEqual(rs, self.toy_exp)

    def test_dump_load(self):
        fd = BIndexer(self.toy_data.shape[1])
        fd.add(self.toy_label, self.toy_data.tobytes())
        fd.dump(self.dump_path)

        fd2 = BIndexer.load(self.dump_path)
        rs = fd2.query(self.toy_query.tobytes())
        self.assertEqual(rs, self.toy_exp)
