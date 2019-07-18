import os
import shutil
import unittest

import numpy as np

from gnes.helper import touch_dir
from gnes.indexer.vector.annoy import AnnoyIndexer


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
        self.assertEqual(a.size, 10)
        top_1 = [i[0][0] for i in a.query(self.toy_data, top_k=1)]
        self.assertEqual(top_1, list(range(10)))
        a.close()
