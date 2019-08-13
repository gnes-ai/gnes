import os
import unittest

import numpy as np

from gnes.indexer.base import JointIndexer
from tests import txt_file2pb_docs


@unittest.SkipTest
class TestJointIndexer(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'indexer.bin')
        self.yaml_path = os.path.join(dirname, 'yaml', 'base-indexer.yml')

        self.n_bytes = 8
        self.query_num = 3

        self.docs = []
        self.querys = []

        self.pb_docs = txt_file2pb_docs(open(os.path.join(dirname, 'tangshi.txt')))

    def test_add(self):
        mhi = JointIndexer.load_yaml(self.yaml_path)

        for doc in self.pb_docs:
            if len(doc.chunks) == 0:
                continue
            mhi.add([doc.doc_id], [doc], [1.])
            vecs = np.random.randint(
                0, 255, [len(doc.chunks), self.n_bytes]).astype(np.uint8)
            mhi.add([(doc.doc_id, j) for j in range(len(doc.chunks))], vecs, [1.] * len(doc.chunks))
            if len(self.querys) < self.query_num:
                self.querys.append(vecs)

        for q in self.querys:
            results = mhi.query(q, top_k=1)
            for topk in results:
                print(topk)
                d, o, w, s, *_ = topk[0]
                self.assertEqual(1.0, s)
        mhi.close()
