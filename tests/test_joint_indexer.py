import os
import unittest

import numpy as np

from gnes.indexer.base import JointIndexer
from gnes.proto import gnes_pb2, array2blob, blob2array
# from gnes.preprocessor.text import txt_file2pb_docs



class TestJointIndexer(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'indexer.bin')
        self.yaml_path = os.path.join(dirname, 'yaml', 'base-indexer.yml')

        # self.n_bytes = 2
        self.query_num = 3
        self.doc_num = 100
        self.doc_size = 5

        self.docs = []
        self.query = None

        self.pb_docs = txt_file2pb_docs(os.path.join(dirname, 'tangshi.txt'))

    def test_add(self):
        mhi = JointIndexer.load_yaml(self.yaml_path)

        for doc in self.pb_docs:
            mhi.add([doc.id], [doc])
            vecs = np.random.random([len(doc.chunks), 100]).astype(np.float32)
            mhi.add([(doc.id, j) for j in range(len(doc.chunks))], vecs)
            if not self.query:
                self.query = vecs

        results = mhi.query(self.querys, top_k=1)
        self.assertEqual(len(results), len(self.querys))
        for topk in results:
            print(topk)
            d, s, *_ = topk[0]
            self.assertEqual(1.0, s)



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
