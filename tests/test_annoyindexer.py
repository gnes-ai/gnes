import os
import unittest

import numpy as np

from gnes.indexer.chunk.annoy import AnnoyIndexer
from gnes.indexer.chunk.numpy import NumpyIndexer


class TestAnnoyIndexer(unittest.TestCase):
    def setUp(self):
        self.toy_data = np.random.random([10, 5]).astype(np.float32)

        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'indexer.pkl')

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)

    def test_search(self):
        a = AnnoyIndexer(5, self.dump_path)
        a.add(list(zip(list(range(10)), list(range(10)))), self.toy_data, [1.] * 10)
        self.assertEqual(a.num_chunks, 10)
        self.assertEqual(a.num_docs, 10)
        top_1 = [i[0][0] for i in a.query(self.toy_data, top_k=1)]
        self.assertEqual(top_1, list(range(10)))
        a.close()
        a.dump()
        a.dump_yaml()

    def test_numpy_indexer(self):
        a = NumpyIndexer()
        a.add(list(zip(list(range(10)), list(range(10)))), self.toy_data, [1.] * 10)
        self.assertEqual(a.num_chunks, 10)
        self.assertEqual(a.num_docs, 10)
        top_1 = [i[0][0] for i in a.query(self.toy_data, top_k=1)]
        self.assertEqual(top_1, list(range(10)))
        a.close()
        a.dump()
        a.dump_yaml()
        b = NumpyIndexer.load_yaml(a.yaml_full_path)
        self.assertEqual(b.num_chunks, 10)
        self.assertEqual(b.num_docs, 10)
        top_1 = [i[0][0] for i in b.query(self.toy_data, top_k=1)]
        self.assertEqual(top_1, list(range(10)))
