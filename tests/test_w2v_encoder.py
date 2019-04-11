import os
import unittest

from gnes.document import UniSentDocument, MultiSentDocument
from gnes.encoder import PipelineEncoder
from gnes.encoder.w2v import W2vEncoder


class TestElmoEncoder(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'w2v_encoder.bin')

        self.test_data1 = UniSentDocument.from_file(
            os.path.join(dirname, 'tangshi.txt'))
        self.test_data2 = MultiSentDocument.from_file(
            os.path.join(dirname, 'tangshi.txt'))
        self.test_str = [s for d in self.test_data1 for s in d.sentences]

    def test_encoding(self):
        w2v_encoder = W2vEncoder(
            model_name='sgns.wiki.bigram-char.sample',
            pooling_strategy="REDUCE_MEAN")
        vec = w2v_encoder.encode(self.test_str)
        self.assertEqual(vec.shape[0], len(self.test_str))
        self.assertEqual(vec.shape[1], 300)

    def test_dump_load(self):
        w2v_encoder = W2vEncoder(
            model_name='sgns.wiki.bigram-char.sample',
            pooling_strategy="REDUCE_MEAN")
        w2v_encoder.dump(self.dump_path)
        w2v_encoder2 = W2vEncoder.load(self.dump_path)
        vec = w2v_encoder2.encode(self.test_str)
        self.assertEqual(vec.shape[0], len(self.test_str))
        self.assertEqual(vec.shape[1], 300)

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)
