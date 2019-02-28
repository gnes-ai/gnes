import os
import time
import unittest

from bert_serving.client import BertClient
from bert_serving.server import BertServer
from bert_serving.server.helper import get_args_parser

from src.nes.encoder.bert_binary import BertBinaryEncoder


class TestBertServing(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)

        with open(os.path.join(dirname, 'tangshi.txt'), encoding='utf8') as fp:
            self.test_data = [v.strip() for v in fp if v.strip() and len(v.strip()) > 10]

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

        bbe = BertBinaryEncoder(port=int(os.environ['BERT_CI_PORT']),
                                port_out=int(os.environ['BERT_CI_PORT_OUT']))
        self.assertRaises(RuntimeError, bbe.encode)

        bbe.train(self.test_data)
        out = bbe.encode(self.test_data)
        bbe.bc_encoder.close()
        self.assertEqual(bytes, type(out))
        self.assertEqual(len(self.test_data) * bbe.num_bytes, len(out))

    def tearDown(self):
        self.server.close()
