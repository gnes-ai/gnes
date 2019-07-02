import os
import shutil
import unittest

import numpy as np

from gnes.indexer.vector.faiss import FaissIndexer


class TestEUIndexer(unittest.TestCase):
    def setUp(self):
        self.toy_query = np.random.random([1000, 20]).astype(np.float32)
        self.toy_label = np.random.randint(0, 1e9, [1000, 2]).tolist()
        self.add_query = np.random.random([1000, 20]).astype(np.float32)
        self.add_label = np.random.randint(0, 1e9, [1000, 2]).tolist()

        self.sub_query = self.toy_query[:10]
        self.data_path = './test_eu_indexer'
        self.dump_path = './test_eu_indexer/indexer.pkl'

    def tearDown(self):
        if os.path.exists(self.data_path):
            shutil.rmtree(self.data_path)

    def test_add(self):
        fd = FaissIndexer(20, 'HNSW32', self.data_path)
        fd.add(self.toy_label, self.toy_query, [1.] * len(self.toy_label))
        self.assertEqual(fd.size, self.toy_query.shape[0])
        fd.add(self.add_label, self.add_query, [1.] * len(self.add_label))
        self.assertEqual(fd.size,
                         self.toy_query.shape[0] + self.add_query.shape[0])

    def test_query(self):
        fd = FaissIndexer(20, 'HNSW32', self.data_path)
        fd.add(self.toy_label, self.toy_query, [1.] * len(self.toy_label))
        ret = fd.query(self.sub_query, top_k=5)
        self.assertEqual(len(ret), self.sub_query.shape[0])
        self.assertEqual(len(ret[0]), 5)

    def test_dump_load(self):
        with FaissIndexer(20, 'HNSW32', self.data_path) as tmp:
            tmp.add(self.toy_label, self.toy_query, [1.] * len(self.toy_label))
            tmp.dump(self.dump_path)

        with FaissIndexer.load(self.dump_path) as fd:
            ret = fd.query(self.sub_query, top_k=2)
            self.assertEqual(len(ret), self.sub_query.shape[0])
            self.assertEqual(len(ret[0]), 2)
