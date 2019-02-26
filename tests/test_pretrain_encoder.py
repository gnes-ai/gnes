import unittest

from src.nes import BaseEncoder


class DummyTrainEncoder(BaseEncoder):
    @BaseEncoder.pretrain_required
    def encode(self, *args, **kwargs):
        pass

    @BaseEncoder.as_pretrain
    def train(self, *args, **kwargs):
        pass


class TestDocument(unittest.TestCase):
    def test_no_pretrain(self):
        a = DummyTrainEncoder()
        self.assertRaises(RuntimeError, a.encode)

    def test_with_pretrian(self):
        a = DummyTrainEncoder()
        a.train()
        a.encode()
