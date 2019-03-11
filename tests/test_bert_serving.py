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

        self.test_data1 = list(UniSentDocument.from_file(os.path.join(dirname, 'tangshi.txt')))
        self.test_data2 = list(MultiSentDocument.from_file(os.path.join(dirname, 'tangshi.txt')))
        self.test_str = [d._content for d in self.test_data1]
        self.port = os.environ.get('BERT_CI_PORT', '7125')
        self.port_out = os.environ.get('BERT_CI_PORT_OUT', '7126')

        args = get_args_parser().parse_args(['-model_dir', os.environ.get('BERT_CI_MODEL', '/chinese_L-12_H-768_A-12'),
                                             '-port', self.port,
                                             '-port_out', self.port_out,
                                             '-max_seq_len', 'NONE',
                                             '-mask_cls_sep',
                                             '-cpu'])
        self.server = BertServer(args)
        self.server.start()
        time.sleep(30)

    def test_bert_client(self):
        bc = BertClient(port=int(self.port),
                        port_out=int(self.port_out))
        vec = bc.encode(self.test_str)
        bc.close()
        self.assertEqual(vec.shape[0], len(self.test_str))
        self.assertEqual(vec.shape[1], 768)

        num_bytes = 8

        bbe = BertBinaryEncoder(num_bytes, pca_output_dim=32,
                                cluster_per_byte=8,
                                port=int(self.port),
                                port_out=int(self.port_out))
        self.assertRaises(RuntimeError, bbe.encode)

        bbe.train(self.test_str)
        out = bbe.encode(self.test_str)
        bbe.close()
        self.assertEqual(bytes, type(out))
        self.assertEqual(len(self.test_str) * num_bytes, len(out))

        bbe.dump(self.dump_path)
        self.assertTrue(os.path.exists(self.dump_path))
        bbe2 = bbe.load(self.dump_path)
        out2 = bbe2.encode(self.test_str)
        self.assertEqual(out, out2)

        nes = DummyNES(num_bytes=8,
                       pca_output_dim=32,
                       cluster_per_byte=8,
                       port=int(self.port),
                       port_out=int(self.port_out),
                       data_path=self.db_path)

        dirname = os.path.dirname(__file__)

        self.assertRaises(RuntimeError, nes.add, self.test_data1)
        self.assertRaises(RuntimeError, nes.query, self.test_data1, 1)

        nes.train(self.test_data1)
        nes.add(self.test_data1)
        query = [s for d in self.test_data1 for s in d.sentences]
        result = nes.query(query, top_k=2)
        self.assertEqual(len(query), len(result))
        self.assertEqual(len(result[0]), 2)
        for q, r in zip(query, result):
            print('q: %s\tr: %s' % (q, r))

        # test dump and loads
        nes.dump(self.dump_path)
        nes.close()
        self.assertTrue(os.path.exists(self.dump_path))
        nes2 = DummyNES.load(self.dump_path)
        result2 = nes2.query(query, top_k=2)
        self.assertEqual(result, result2)
        nes2.close()

        # test multi-sent document
        nes3 = DummyNES(pca_output_dim=32,
                        cluster_per_byte=8,
                        port=int(self.port),
                        port_out=int(self.port_out),
                        data_path=self.db_path)
        nes3.train(self.test_data2)

        # TODO: the next add fails for some unknown reason

        nes3.add(self.test_data2)
        query = [s for d in self.test_data2 for s in d.sentences]
        result = nes3.query(query, top_k=2)
        self.assertEqual(len(query), len(result))
        self.assertEqual(len(result[0]), 2)
        # for q, r in zip(query, result):
        #     print('q: %s\tr: %s' % (q, r))

    def tearDown(self):
        self.server.close()
        # wait until all socket close safely
        time.sleep(5)
