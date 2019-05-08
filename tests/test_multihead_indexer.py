import os
import unittest

import numpy as np

from gnes.indexer.base import MultiheadIndexer
from gnes.proto import gnes_pb2, array2blob


class TestMHIndexer(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'indexer.bin')
        self.yaml_path = os.path.join(dirname, 'yaml', 'base-indexer.yml')
        self.n_bytes = 2
        self.query_num = 3

        self.querys = []
        self.docs = []
        self.chunk_keys = []
        self.chunk_bins = []
        with open(os.path.join(dirname, 'tangshi.txt')) as f:
            title = ''
            sents = []
            doc_id = 0
            for line in f:
                line = line.strip()

                if line and not title:
                    title = line
                    sents.append(line)
                elif not line and title:
                    doc = gnes_pb2.Document()
                    doc.id = doc_id
                    doc.text = ' '.join(sents)
                    for i, sent in enumerate(sents):
                        chunk = doc.chunks.add()
                        x = np.random.randint(
                            0, 255, [1, self.n_bytes]).astype(np.uint8)
                        self.chunk_bins.append(x)
                        self.chunk_keys.append((doc_id, i))
                        if len(self.querys) < self.query_num:
                            self.querys.append(x)
                        chunk.text = sent
                        chunk.blob.CopyFrom(array2blob(x))

                    doc.is_parsed = True
                    doc.is_encoded = True
                    doc_id += 1
                    sents.clear()
                    title = ''
                    self.docs.append(doc)
        self.chunk_bins = np.concatenate(self.chunk_bins, axis=0)
        self.querys = np.concatenate(self.querys, axis=0)

    # def test_load(self):
    #     mhi = MultiheadIndexer.load_yaml(self.yaml_path)
    #     mhi.close()

    def test_add(self):
        mhi = MultiheadIndexer.load_yaml(self.yaml_path)
        mhi.add(range(len(self.docs)), self.docs, head_name='doc_indexer')
        mhi.add(
            self.chunk_keys,
            self.chunk_bins.tobytes(),
            head_name='binary_indexer')

        mhi.query(self.querys.tobytes(), top_k=1)

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
