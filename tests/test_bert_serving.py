import os
import time
import unittest

from bert_serving.client import BertClient
from bert_serving.server import BertServer
from bert_serving.server.helper import get_args_parser

from src.nes.encoder.bert_binary import BertBinaryEncoder


class TestBertServing(unittest.TestCase):

    def setUp(self):
        args = get_args_parser().parse_args(['-model_dir', os.environ['BERT_CI_MODEL'],
                                             '-port', os.environ['BERT_CI_PORT'],
                                             '-port_out', os.environ['BERT_CI_PORT_OUT'],
                                             '-max_seq_len', 'NONE',
                                             '-mask_cls_sep'])
        self.server = BertServer(args)
        self.server.start()
        time.sleep(30)
        with open('data/tangshi.txt') as fp:
            self.test_data = [v.strip() for v in fp if v.strip()]
        print('load %d lines of sentences' % len(self.test_data))

    def test_bert_client(self):
        bc = BertClient(timeout=2000, port=int(os.environ['BERT_CI_PORT']),
                        port_out=int(os.environ['BERT_CI_PORT_OUT']))
        vec = bc.encode(['你好么？我很好', '你好么？我很好!但 我还没吃'])
        self.assertEqual(vec.shape[0], 2)
        self.assertEqual(vec.shape[1], 768)

    def test_bert_binary_encoder(self):
        bbe = BertBinaryEncoder(port=int(os.environ['BERT_CI_PORT']),
                                port_out=int(os.environ['BERT_CI_PORT_OUT']),
                                timeout=10000)  # set timeout larger as we do actual encoding
        self.assertRaises(RuntimeError, bbe.encode)

        bbe.train(self.test_data)
        out = bbe.encode(self.test_data)
        self.assertEqual(bytes, type(out))
        self.assertEqual(len(self.test_data) * bbe.num_bytes, len(out))

    def tearDown(self):
        self.server.close()
