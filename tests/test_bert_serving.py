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
        self.bbe_path = os.path.join(dirname, 'yaml',
                                     'bert-binary-encoder.yml')

        self.port = os.environ.get('BERT_CI_PORT', '7125')
        self.port_out = os.environ.get('BERT_CI_PORT_OUT', '7126')

        args = get_args_parser().parse_args([
            '-model_dir',
            os.environ.get('BERT_CI_MODEL', '/chinese_L-12_H-768_A-12'),
            '-port', self.port, '-port_out', self.port_out, '-max_seq_len',
            'NONE', '-mask_cls_sep', '-pooling_layer', '-12', '-cpu'
        ])
        self.server = BertServer(args)
        self.server.start()
        self.server.is_ready.wait()

        self.test_docs = []
        self.test_sents = []

        with open(os.path.join(dirname, 'tangshi.txt')) as f:
            for line in f:
                line = line.strip()
                if line:
                    self.test_sents.append(line)

    def test_bert_client(self):
        bc = BertClient(port=int(self.port), port_out=int(self.port_out))
        vec = bc.encode(self.test_sents)
        bc.close()
        self.assertEqual(vec.shape[0], len(self.test_sents))
        self.assertEqual(vec.shape[1], 768)

    def test_bert_binary_encoder(self):

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

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)
