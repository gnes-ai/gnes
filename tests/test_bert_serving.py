import os
import time
import unittest

from bert_serving.client import BertClient
from bert_serving.server import BertServer
from bert_serving.server.helper import get_args_parser

from src.nes import DummyNES
from src.nes.document import UniSentDocument, MultiSentDocument
from src.nes.encoder.bert_binary import BertBinaryEncoder


class TestBertServing(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'encoder.bin')
        self.db_path = './test_leveldb'

        with open(os.path.join(dirname, 'tangshi.txt'), encoding='utf8') as fp:
            self.test_data = [v.strip() for v in fp if v.strip() and len(v.strip()) > 10]
            tmp = self.test_data
            self.test_data1 = [UniSentDocument(t) for t in tmp]
            self.test_data2 = [MultiSentDocument(t) for t in tmp]

        print('load %d lines of sentences' % len(self.test_data))

        args = get_args_parser().parse_args(['-model_dir', os.environ['BERT_CI_MODEL'],
                                             '-port', os.environ['BERT_CI_PORT'],
                                             '-port_out', os.environ['BERT_CI_PORT_OUT'],
                                             '-max_seq_len', 'NONE',
                                             '-mask_cls_sep',
                                             '-cpu'])
        self.server = BertServer(args)
        self.server.start()
        time.sleep(30)

    def test_bert_client(self):
        bc = BertClient(port=int(os.environ['BERT_CI_PORT']),
                        port_out=int(os.environ['BERT_CI_PORT_OUT']))
        vec = bc.encode(self.test_data)
        bc.close()
        self.assertEqual(vec.shape[0], len(self.test_data))
        self.assertEqual(vec.shape[1], 768)

        bbe = BertBinaryEncoder(pca_output_dim=32,
                                cluster_per_byte=8,
                                port=int(os.environ['BERT_CI_PORT']),
                                port_out=int(os.environ['BERT_CI_PORT_OUT']))
        self.assertRaises(RuntimeError, bbe.encode)

        bbe.train(self.test_data)
        out = bbe.encode(self.test_data)
        bbe.bc_encoder.close()
        self.assertEqual(bytes, type(out))
        self.assertEqual(len(self.test_data) * bbe.num_bytes, len(out))

        bbe.dump(self.dump_path)
        self.assertTrue(os.path.exists(self.dump_path))
        bbe2 = bbe.load(self.dump_path)
        out2 = bbe2.encode(self.test_data)
        self.assertEqual(out, out2)

        nes = DummyNES(pca_output_dim=32,
                       cluster_per_byte=8,
                       port=int(os.environ['BERT_CI_PORT']),
                       port_out=int(os.environ['BERT_CI_PORT_OUT']),
                       data_path=self.db_path)
        self.assertRaises(RuntimeError, nes.add, self.test_data1)
        self.assertRaises(RuntimeError, nes.query, self.test_data1, 1)
        nes.train(self.test_data1)
        nes.add(self.test_data1)
        query = [s for d in self.test_data1 for s in d.sentences]
        print(nes.query(query, top_k=1))

    def tearDown(self):
        self.server.close()
        # wait until all socket close safely
        time.sleep(5)
