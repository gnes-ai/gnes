import unittest

from gnes.encoder.base import BaseEncoder as BE, PipelineEncoder
from gnes.helper import train_required


class _DummyTrainEncoder(BE):
    @train_required
    def encode(self, *args, **kwargs):
        pass

    def train(self, *args, **kwargs):
        pass


class _BertEncoder(BE):
    def encode(self, data, *args, **kwargs):
        print('bert-encode!')
        return data * 7

    def train(self, data, *args, **kwargs):
        print('bert-train!')


class _PQEncoder(BE):
    def encode(self, data, *args, **kwargs):
        print('pq-encode!')
        return data * 2

    def train(self, data, *args, **kwargs):
        print('pq-train!')


class _PCAEncoder(BE):
    @train_required
    def encode(self, data, *args, **kwargs):
        print('pca-encode!')
        return data + 3

    def train(self, data, *args, **kwargs):
        print('pca-train!')


class _LOPQEncoder(PipelineEncoder):
    def __init__(self):
        super().__init__()
        self.components = lambda: [_PCAEncoder(), _PQEncoder()]


class _BertBinaryEncoder(PipelineEncoder):
    def __init__(self):
        super().__init__()
        self.components = lambda: [_BertEncoder(), _LOPQEncoder()]


class TestDocument(unittest.TestCase):
    def test_no_pretrain(self):
        a = _DummyTrainEncoder()
        self.assertRaises(RuntimeError, a.encode)

    def test_with_pretrain(self):
        a = _DummyTrainEncoder()
        a.train()
        a.encode()

    def test_hierachy_encoder(self):
        le = _LOPQEncoder()
        self.assertRaises(RuntimeError, le.encode, 1)
        le.train(data=1)
        self.assertEqual(le.encode(data=1), 8)
        self.assertEqual(le.encode(data=2), 10)

    def test_hierachy_encoder2(self):
        print('___')
        le2 = _BertBinaryEncoder()
        le2.train(data=1)
        le2.encode(data=1)
