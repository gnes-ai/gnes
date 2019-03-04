import os
import time
import unittest

from bert_serving.server import BertServer
from bert_serving.server.helper import get_args_parser

from src.nes import DummyNES
from src.nes.document import UniSentDocument, MultiSentDocument


class TestBertServing(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.db_path = './test_leveldb'
        self.dump_path = os.path.join(dirname, 'nes.bin')

        with open(os.path.join(dirname, 'tangshi.txt'), encoding='utf8') as fp:
            tmp = [v.strip() for v in fp if v.strip() and len(v.strip()) > 10]
            self.test_data1 = [UniSentDocument(t) for t in tmp]
            self.test_data2 = [MultiSentDocument(t) for t in tmp]

        print('load %d lines of sentences' % len(tmp))

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
