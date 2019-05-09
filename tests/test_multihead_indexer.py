import os
import unittest

import numpy as np

from gnes.indexer.base import MultiheadIndexer
from gnes.proto import gnes_pb2, array2blob, blob2array


class TestMHIndexer(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'indexer.bin')
        self.yaml_path = os.path.join(dirname, 'yaml', 'base-indexer.yml')
        self.n_bytes = 2
        self.query_num = 3

        self.querys = None
        self.docs = []
        self.chunk_keys = []
        with open(os.path.join(dirname, 'tangshi.txt')) as f:
            title = ''
            sents = []
            doc_id = 0
            for line in f:
                line = line.strip()

                if line and not title:
                    title = line
                    sents.append(line)
                elif line and title:
                    sents.append(line)
                elif not line and title and len(sents) > 1:
                    doc = gnes_pb2.Document()
                    doc.id = doc_id
                    doc.text = ' '.join(sents)
                    doc.text_chunks.extend(sents)
                    x = np.random.randint(
                            0, 255, [len(sents), self.n_bytes]).astype(np.uint8)
                    doc.encodes.CopyFrom(array2blob(x))

                    if self.querys is None:
                        self.querys = x[:self.query_num]

                    doc.is_parsed = True
                    doc.is_encoded = True
                    doc_id += 1
                    sents.clear()
                    title = ''
                    self.docs.append(doc)

    # def test_load(self):
    #     mhi = MultiheadIndexer.load_yaml(self.yaml_path)
    #     mhi.close()

    def test_add(self):
        mhi = MultiheadIndexer.load_yaml(self.yaml_path)
        mhi.add(range(len(self.docs)), self.docs, head_name='doc_indexer')
        for doc in self.docs:
            mhi.add([(doc.id, i) for i in range(len(doc.text_chunks))], blob2array(doc.encodes).tobytes(), head_name='binary_indexer')

        results = mhi.query(self.querys.tobytes(), top_k=1)
        self.assertEqual(len(results), len(self.querys))
        for topk in results:
            d, s = topk[0]
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
