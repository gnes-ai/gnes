import os
import unittest

import numpy as np

from gnes.indexer.base import MultiheadIndexer


class TestMHIndexer(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'indexer.bin')
        self.yaml_path = os.path.join(dirname, 'yaml', 'base-indexer.yml')
        self.sent_keys = [1, 2, 3, 4, 5, 6]
        self.sent_bin = np.array([[1, 2],
                                  [1, 2],
                                  [1, 2],
                                  [2, 1],
                                  [2, 1],
                                  [2, 1]]).astype(np.uint8)
        self.doc_keys = [1, 1, 1, 2, 2, 2]
        self.doc_keys_uniq = [1, 2]
        self.doc_content = ['d1', 'd2']
        self.query1 = np.array([1, 2]).astype(np.uint8)
        self.query2 = np.array([2, 1]).astype(np.uint8)
        self.query1and2 = np.array([[1, 2], [2, 1]]).astype(np.uint8)

    def test_load(self):
        MultiheadIndexer.load_yaml(self.yaml_path)

    def test_add(self):
        mhi = MultiheadIndexer.load_yaml(self.yaml_path)
        mhi.add(self.sent_keys, self.doc_keys, head_name='sent_doc_indexer')
        mhi.add(self.doc_keys_uniq, self.doc_content, head_name='doc_content_indexer')
        mhi.add(self.sent_keys, self.sent_bin.tobytes(), head_name='binary_indexer')

        self.assertEqual(mhi.query(self.query1.tobytes(), top_k=1), [[('d1', 0)]])
        self.assertEqual(mhi.query(self.query2.tobytes(), top_k=1), [[('d2', 0)]])

        self.assertEqual(mhi.query(self.query1.tobytes(), top_k=2), [[('d1', 0), ('d2', 0)]])
        self.assertEqual(mhi.query(self.query2.tobytes(), top_k=2), [[('d2', 0), ('d1', 0)]])

        self.assertEqual(mhi.query(self.query1and2.tobytes(), top_k=1), [[('d1', 0)], [('d2', 0)]])
        self.assertEqual(mhi.query(self.query1and2.tobytes(), top_k=2),
                         [[('d1', 0), ('d2', 0)], [('d2', 0), ('d1', 0)]])
