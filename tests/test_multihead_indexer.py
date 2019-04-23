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
        self.doc_content = [dict(id=1, content='d1',
                                 sentences=['d11', 'd12', 'd13'],
                                 sentence_ids=[1, 2, 3]),
                            dict(id=2, content='d2',
                                 sentences=['d21', 'd22', 'd23'],
                                 sentence_ids=[4, 5, 6])]
        self.query1 = np.array([1, 2]).astype(np.uint8)
        self.query2 = np.array([2, 1]).astype(np.uint8)
        self.query1and2 = np.array([[1, 2], [2, 1]]).astype(np.uint8)

    def test_load(self):
        mhi = MultiheadIndexer.load_yaml(self.yaml_path)
        mhi.close()

    def test_add(self):
        mhi = MultiheadIndexer.load_yaml(self.yaml_path)
        mhi.add(self.sent_keys, self.doc_keys, head_name='sent_doc_indexer')
        mhi.add(self.doc_keys_uniq, self.doc_content, head_name='doc_content_indexer')
        mhi.add(self.sent_keys, self.sent_bin.tobytes(), head_name='binary_indexer')

        self.assertEqual(mhi.query(self.query1.tobytes(), top_k=1, return_field=('id',)),
                         [[({'id': self.doc_content[0]['id']}, 1.0)]])
        self.assertEqual(
            mhi.query(self.query1.tobytes(), top_k=1,
                      return_field=('id', 'content', 'sentences', 'sentence_ids')),
            [[(self.doc_content[0], 1.0)]])
        self.assertEqual(
            mhi.query(self.query1.tobytes(), top_k=1,
                      return_field=None),
            [[(self.doc_content[0], 1.0)]])
        self.assertEqual(mhi.query(self.query2.tobytes(), top_k=1, return_field=None), [[(self.doc_content[1], 1.0)]])

        self.assertEqual(mhi.query(self.query1.tobytes(), top_k=2, return_field=None),
                         [[(self.doc_content[0], 1.0), (self.doc_content[1], 0.)]])
        self.assertEqual(mhi.query(self.query2.tobytes(), top_k=2, return_field=None),
                         [[(self.doc_content[1], 1.0), (self.doc_content[0], 0.)]])

        self.assertEqual(mhi.query(self.query1and2.tobytes(), top_k=1, return_field=None),
                         [[(self.doc_content[0], 1.0)], [(self.doc_content[1], 1.0)]])
        self.assertEqual(mhi.query(self.query1and2.tobytes(), top_k=2, return_field=None),
                         [[(self.doc_content[0], 1.0), (self.doc_content[1], 0.0)],
                          [(self.doc_content[1], 1.0), (self.doc_content[0], 0.0)]])
        mhi.close()
