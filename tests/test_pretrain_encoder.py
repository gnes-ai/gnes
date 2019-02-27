import unittest

from src.nes import BaseEncoder as BE


class DummyTrainEncoder(BE):
    @BE._train_required
    def encode(self, *args, **kwargs):
        pass

    @BE._as_train_func
    def train(self, *args, **kwargs):
        pass


class TestDocument(unittest.TestCase):
    def test_no_pretrain(self):
        a = DummyTrainEncoder()
        self.assertRaises(RuntimeError, a.encode)

    def test_with_pretrain(self):
        a = DummyTrainEncoder()
        a.train()
        a.encode()
