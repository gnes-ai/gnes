import os
import shutil
import unittest

import numpy as np

from gnes.helper import touch_dir
from gnes.indexer.vector.annoy import AnnoyIndexer


class TestAnnoyIndexer(unittest.TestCase):
    def setUp(self):
        self.toy_data = np.random.random([10, 5]).astype(np.float32)

        self.data_path = './test_bindexer_data'
        touch_dir(self.data_path)
        self.dump_path = os.path.join(self.data_path, 'indexer.pkl')

    def tearDown(self):
        if os.path.exists(self.data_path):
            shutil.rmtree(self.data_path)
            # os.remove(self.data_path)

    def test_search(self):
        a = AnnoyIndexer(5, self.data_path)
        a.add(list(zip(list(range(10)), list(range(10)))), self.toy_data, [1.] * 10)
        self.assertEqual(a.size, 10)
        top_1 = [i[0][0] for i in a.query(self.toy_data, top_k=1)]
        self.assertEqual(top_1, list(range(10)))
        a.close()
