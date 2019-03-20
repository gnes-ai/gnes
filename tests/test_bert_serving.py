import os
import time
import unittest
from shutil import rmtree

from bert_serving.client import BertClient
from bert_serving.server import BertServer
from bert_serving.server.helper import get_args_parser

from gnes import GNES, PipelineEncoder
from gnes.document import UniSentDocument, MultiSentDocument


class TestBertServing(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'encoder.bin')
        self.bbe_path = os.path.join(dirname, 'yaml', 'bert-binary-encoder.yml')
        self.nes_path = os.path.join(dirname, 'yaml', 'base-nes.yml')
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
                                             '-pooling_layer', '-12',
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

        bbe = PipelineEncoder.load_yaml(self.bbe_path)
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

        nes = GNES.load_yaml(self.nes_path)

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
        nes2 = GNES.load(self.dump_path)
        result2 = nes2.query(query, top_k=2)
        self.assertEqual(result, result2)
        nes2.close()

        # test multi-sent document
        nes3 = GNES.load_yaml(self.nes_path)
        nes3.train(self.test_data2)

        # TODO: the next add fails for some unknown reason

        nes3.add(self.test_data2)
        query = [s for d in self.test_data2 for s in d.sentences]
        result = nes3.query(query, top_k=2)

        self.assertEqual(len(query), len(result))
        self.assertEqual(len(result[0]), 2)
        nes3.close()
        # for q, r in zip(query, result):
        #     print('q: %s\tr: %s' % (q, r))

    def tearDown(self):
        if os.path.exists(self.db_path):
            rmtree(self.db_path)
        self.server.close()
        # wait until all socket close safely
        time.sleep(5)
