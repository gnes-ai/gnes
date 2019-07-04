import os
import shutil
import unittest

import numpy as np

from gnes.helper import touch_dir
from gnes.indexer.vector.bindexer import BIndexer


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

        self.toy_exp = [[(234, 0, 1., 4,), (123, 1, 1., 4)], [(432, 0, 1., 4), (1, 0, 1., 4)],
                        [(234, 0, 1., 3), (123, 1, 1., 3)]]
        self.weights = [1.] * len(self.toy_label)

        self.data_path = './test_bindexer_data'
        touch_dir(self.data_path)
        self.dump_path = os.path.join(self.data_path, 'indexer.pkl')

    def tearDown(self):
        if os.path.exists(self.data_path):
            shutil.rmtree(self.data_path)
            # os.remove(self.data_path)

    def test_nsw_search(self):
        fd = BIndexer(self.toy_data.shape[1], data_path=self.data_path + "_1")
        fd.add(self.toy_label, self.toy_data, self.weights)

        rs = fd.query(self.toy_query, 2, method='nsw', normalized_score=False)
        for i in range(len(rs)):
            rs[i] = sorted(rs[i], key=lambda x: (x[3], -x[0]))
        fd.close()
        shutil.rmtree(self.data_path + "_1")
        self.assertEqual(rs, self.toy_exp)

    def test_force_search(self):
        fd = BIndexer(self.toy_data.shape[1], data_path=self.data_path + "_2")
        fd.add(self.toy_label, self.toy_data, self.weights)
        rs = fd.query(self.toy_query, 2, method='force', normalized_score=False)
        for i in range(len(rs)):
            rs[i] = sorted(rs[i], key=lambda x: (x[3], -x[0]))
        fd.close()
        shutil.rmtree(self.data_path + "_2")
        self.assertEqual(rs, self.toy_exp)

    def test_dump_load(self):
        fd = BIndexer(self.toy_data.shape[1], data_path=self.data_path + "_3")
        fd.add(self.toy_label, self.toy_data, self.weights)
        fd.dump(self.dump_path)
        fd.close()
        # shutil.rmtree(self.data_path + "_3")

        fd2 = BIndexer.load(self.dump_path)
        rs = fd2.query(self.toy_query, 2, normalized_score=False)
        for i in range(len(rs)):
            rs[i] = sorted(rs[i], key=lambda x: (x[3], -x[0]))
        fd2.close()

        shutil.rmtree(self.data_path + "_3")
        self.assertEqual(rs, self.toy_exp)
