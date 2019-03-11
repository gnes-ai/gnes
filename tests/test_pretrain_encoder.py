import unittest

from src.nes import BaseEncoder as BE, PipelineEncoder


class DummyTrainEncoder(BE):
    @BE._train_required
    def encode(self, *args, **kwargs):
        pass

    @BE._as_train_func
    def train(self, *args, **kwargs):
        pass


class BertEncoder(BE):
    def encode(self, data, *args, **kwargs):
        print('bert-encode!')
        return data * 7

    def train(self, data, *args, **kwargs):
        print('bert-train!')


class PQEncoder(BE):
    def encode(self, data, *args, **kwargs):
        print('pq-encode!')
        return data * 2

    def train(self, data, *args, **kwargs):
        print('pq-train!')


class PCAEncoder(BE):
    def encode(self, data, *args, **kwargs):
        print('pca-encode!')
        return data + 3

    def train(self, data, *args, **kwargs):
        print('pca-train!')


class LOPQEncoder(PipelineEncoder):
    def __init__(self):
        super().__init__()
        self.pipeline = [PCAEncoder(), PQEncoder()]


class BertBinaryEncoder(PipelineEncoder):
    def __init__(self):
        super().__init__()
        self.pipeline = [BertEncoder(), LOPQEncoder()]


class TestDocument(unittest.TestCase):
    def test_no_pretrain(self):
        a = DummyTrainEncoder()
        self.assertRaises(RuntimeError, a.encode)

    def test_with_pretrain(self):
        a = DummyTrainEncoder()
        a.train()
        a.encode()

    def test_hierachy_encoder(self):
        le = LOPQEncoder()
        self.assertRaises(RuntimeError, le.encode, 1)
        le.train(data=1)
        self.assertEqual(le.encode(data=1), 8)
        self.assertEqual(le.encode(data=2), 10)

    def test_hierachy_encoder2(self):
        print('___')
        le2 = BertBinaryEncoder()
        le2.train(data=1)
        le2.encode(data=1)
