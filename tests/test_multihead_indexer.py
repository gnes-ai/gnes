import os
import unittest

import numpy as np

from gnes.indexer.base import JointIndexer
from gnes.proto import gnes_pb2, array2blob, blob2array
from gnes.preprocessor.text import txt_file2pb_docs



class TestJointIndexer(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'indexer.bin')
        self.yaml_path = os.path.join(dirname, 'yaml', 'base-indexer.yml')
        self.n_bytes = 2
        self.query_num = 3

        self.querys = None
        self.docs = []
        self.chunk_keys = []

        self.pb_docs = txt_file2pb_docs(os.path.join(dirname, 'tangshi.txt'))

    def test_add(self):
        mhi = JointIndexer.load_yaml(self.yaml_path)
        mhi.add(range(len(self.docs)), self.docs, head_name='doc_indexer')
        for doc in self.docs:
            mhi.add([(doc.id, i) for i in range(doc.doc_size)], blob2array(doc.encodes), head_name='binary_indexer')

        # results = mhi.query(self.querys, top_k=1)
        # self.assertEqual(len(results), len(self.querys))
        # for topk in results:
        #     print(topk)
        #     d, s, *_ = topk[0]
        #     self.assertEqual(1.0, s)



        # self.assertEqual(mhi.query(self.query1.tobytes(), top_k=1, return_field=('id',)),
        #                  [[({'id': self.doc_content[0]['id']}, 1.0)]])
        # self.assertEqual(
        #     mhi.query(self.query1.tobytes(), top_k=1,
        #               return_field=('id', 'content', 'sentences', 'sentence_ids')),
        #     [[(self.doc_content[0], 1.0)]])
        # self.assertEqual(
        #     mhi.query(self.query1.tobytes(), top_k=1,
        #               return_field=None),
        #     [[(self.doc_content[0], 1.0)]])
        # self.assertEqual(mhi.query(self.query2.tobytes(), top_k=1, return_field=None), [[(self.doc_content[1], 1.0)]])

        # self.assertEqual(mhi.query(self.query1.tobytes(), top_k=2, return_field=None),
        #                  [[(self.doc_content[0], 1.0), (self.doc_content[1], 0.)]])
        # self.assertEqual(mhi.query(self.query2.tobytes(), top_k=2, return_field=None),
        #                  [[(self.doc_content[1], 1.0), (self.doc_content[0], 0.)]])

        # self.assertEqual(mhi.query(self.query1and2.tobytes(), top_k=1, return_field=None),
        #                  [[(self.doc_content[0], 1.0)], [(self.doc_content[1], 1.0)]])
        # self.assertEqual(mhi.query(self.query1and2.tobytes(), top_k=2, return_field=None),
        #                  [[(self.doc_content[0], 1.0), (self.doc_content[1], 0.0)],
        #                   [(self.doc_content[1], 1.0), (self.doc_content[0], 0.0)]])
        mhi.close()
