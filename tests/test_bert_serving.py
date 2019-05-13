import os
import unittest
import numpy as np
from numpy.testing import assert_array_equal
from shutil import rmtree

from bert_serving.client import BertClient
from bert_serving.server import BertServer
from bert_serving.server.helper import get_args_parser

from gnes.encoder.base import PipelineEncoder
from gnes.module.gnes import GNES
from gnes.proto import gnes_pb2


class TestBertServing(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'encoder.bin')
        self.bbe_path = os.path.join(dirname, 'yaml', 'bert-binary-encoder.yml')
        self.nes_path = os.path.join(dirname, 'yaml', 'base-nes.yml')
        self.db_path = './test_leveldb'

        # self.test_data1 = UniSentDocument.from_file(os.path.join(dirname, 'tangshi.txt'))
        # self.test_data2 = MultiSentDocument.from_file(os.path.join(dirname, 'tangshi.txt'))
        # self.test_str = [s for d in self.test_data1 for s in d.sentences]
        self.port = os.environ.get('BERT_CI_PORT', '7125')
        self.port_out = os.environ.get('BERT_CI_PORT_OUT', '7126')

        args = get_args_parser().parse_args(['-model_dir', os.environ.get('BERT_CI_MODEL', '/chinese_L-12_H-768_A-12'),
                                             '-port', self.port,
                                             '-port_out', self.port_out,
                                             '-max_seq_len', 'NONE',
                                             '-mask_cls_sep',
                                             '-pooling_layer', '-12',
                                             '-cpu'])
        self.server = BertServer(args)
        self.server.start()
        self.server.is_ready.wait()

        self.test_querys = []
        self.test_docs = []
        self.test_sents = []

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
                    doc.doc_size = len(sents)

                    doc.is_parsed = True
                    doc.is_encoded = False
                    doc_id += 1

                    self.test_docs.append(doc)
                    self.test_sents.extend(sents)

                    sents.clear()
                    title = ''


    def test_bert_client(self):
        bc = BertClient(port=int(self.port),
                        port_out=int(self.port_out))
        vec = bc.encode(self.test_sents)
        bc.close()
        self.assertEqual(vec.shape[0], len(self.test_sents))
        self.assertEqual(vec.shape[1], 768)

        num_bytes = 8

        bbe = PipelineEncoder.load_yaml(self.bbe_path)
        self.assertRaises(RuntimeError, bbe.encode, self.test_sents)

        bbe.train(self.test_sents)
        out = bbe.encode(self.test_sents)
        bbe.close()
        self.assertEqual(np.ndarray, type(out))
        self.assertEqual(num_bytes, out.shape[1])
        self.assertEqual(len(self.test_sents), len(out))

        bbe.dump(self.dump_path)
        self.assertTrue(os.path.exists(self.dump_path))
        bbe2 = bbe.load(self.dump_path)
        out2 = bbe2.encode(self.test_sents)
        assert_array_equal(out, out2)

        nes = GNES.load_yaml(self.nes_path)

        # self.assertRaises(RuntimeError, nes.add, self.test_docs)
        # self.assertRaises(RuntimeError, nes.query, self.test_data1, 1)

        nes.train(self.test_docs)
        nes.add(self.test_docs)

        # query = [s for d in self.test_data1 for s in d.sentences]
        result = nes.query(self.test_sents, top_k=2)
        self.assertEqual(len(self.test_sents), len(result))
        self.assertEqual(len(result[0]), 2)
        for q, r in zip(self.test_sents, result):
            print('q: %s\tr: %s' % (q, r))

        # test dump and loads
        nes.dump(self.dump_path)
        nes.close()
        self.assertTrue(os.path.exists(self.dump_path))
        nes2 = GNES.load(self.dump_path)
        result2 = nes2.query(self.test_sents, top_k=2)
        self.assertEqual(result, result2)
        nes2.close()



    def tearDown(self):
        if os.path.exists(self.db_path):
            rmtree(self.db_path)
        self.server.close()
