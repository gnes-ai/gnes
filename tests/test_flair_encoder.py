import os
import unittest
import numpy as np
from shutil import rmtree

from gnes.encoder.base import PipelineEncoder
from gnes.encoder.flair import FlairEncoder
from gnes.module.gnes import GNES
from gnes.proto import gnes_pb2


class TestElmoEncoder(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'flair_encoder.bin')
        self.ebe_path = os.path.join(dirname, 'yaml', 'flair-binary-encoder.yml')
        self.nes_path = os.path.join(dirname, 'yaml', 'base-flair-nes.yml')
        self.db_path = './test_leveldb'

        self.test_docs = []
        self.test_str = []
        with open(os.path.join(dirname, 'sonnets.txt')) as f:
            sents = []
            doc_id = 0
            for line in f:
                line = line.strip()

                if line:
                    sents.append(line)

                elif not line and len(sents) > 1:
                    self.test_str.extend(sents)
                    doc = gnes_pb2.Document()
                    doc.id = doc_id
                    doc.text = ' '.join(sents)
                    doc.text_chunks.extend(sents)
                    doc.doc_size = len(sents)

                    doc.is_parsed = True
                    doc.is_encoded = True
                    doc_id += 1
                    sents.clear()
                    self.test_docs.append(doc)

    def test_encoding(self):
        flair_encoder = FlairEncoder(
            model_name=os.environ.get('FLAIR_CI_MODEL'),
            pooling_strategy="REDUCE_MEAN")
        vec = flair_encoder.encode(self.test_str)
        self.assertEqual(vec.shape[0], len(self.test_str))
        self.assertEqual(vec.shape[1], 512)

        num_bytes = 8

        ebe = PipelineEncoder.load_yaml(self.ebe_path)
        self.assertRaises(RuntimeError, ebe.encode, self.test_str)

        ebe.train(self.test_str)
        out = ebe.encode(self.test_str)
        ebe.close()
        self.assertEqual(np.ndarray, type(out))
        self.assertEqual(num_bytes, out.shape[1])
        self.assertEqual(len(self.test_str), len(out))

        ebe.dump(self.dump_path)
        self.assertTrue(os.path.exists(self.dump_path))
        ebe2 = ebe.load(self.dump_path)
        out2 = ebe2.encode(self.test_str)
        # TODO: fix this
        # self.assertEqual(out, out2)

        nes = GNES.load_yaml(self.nes_path)

        self.assertRaises(RuntimeError, nes.add, self.test_docs)
        self.assertRaises(RuntimeError, nes.query, self.test_str, 1)

        nes.train(self.test_docs)
        nes.add(self.test_docs)
        query = self.test_docs[0].text_chunks
        result = nes.query(query, top_k=2)
        self.assertEqual(len(query), len(result))
        self.assertEqual(len(result[0]), 2)
        for q, r in zip(query, result):
            print('q: %s\tr: %s' % (q, r))

        # test dump and loads
        nes.dump(self.dump_path)
        nes.close()
        self.assertTrue(os.path.exists(self.dump_path))
        nes2 = GNES.load(self.dump_path)
        result2 = nes2.query(query, top_k=2)
        # self.assertEqual(result, result2)
        nes2.close()

    def tearDown(self):
        if os.path.exists(self.db_path):
            rmtree(self.db_path)
