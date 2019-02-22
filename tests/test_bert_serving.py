import os
import time
import unittest

from bert_serving.client import BertClient
from bert_serving.server import BertServer
from bert_serving.server.helper import get_args_parser


class TestBertServing(unittest.TestCase):

    def setUp(self):
        args = get_args_parser().parse_args(['-model_dir', os.environ['BERT_CI_MODEL'],
                                             '-port', os.environ['BERT_CI_PORT'],
                                             '-port_out', os.environ['BERT_CI_PORT_OUT']])
        self.server = BertServer(args)
        self.server.start()
        time.sleep(30)

    def test_bert_client(self):
        bc = BertClient(timeout=2000, port=int(os.environ['BERT_CI_PORT']),
                        port_out=int(os.environ['BERT_CI_PORT_OUT']))
        vec = bc.encode(['你好么？我很好', '你好么？我很好!但 我还没吃'])
        self.assertEqual(vec.shape[0], 2)
        self.assertEqual(vec.shape[1], 768)

    def tearDown(self):
        self.server.close()
