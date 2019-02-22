import unittest

from bert_serving.client import BertClient


class TestBertServing(unittest.TestCase):
    def test_bert_client(self):
        bc = BertClient(timeout=2000)
        vec = bc.encode(['你好么？我很好', '你好么？我很好!但 我还没吃'])
        self.assertEqual(vec.shape[0], 2)
        self.assertEqual(vec.shape[1], 768)
