import ctypes
import os
import unittest

from src.nes.document import UniSentDocument, MultiSentDocument


class TestDocument(unittest.TestCase):
    def test_uni_sent_doc(self):
        d = UniSentDocument('你好么？我很好')
        self.assertLessEqual(d.id, ctypes.c_uint(-1).value)
        self.assertGreaterEqual(d.id, 0)
        self.assertEqual(len(list(d.sentences)), 1)

    def test_multi_sent_doc(self):
        d = MultiSentDocument('你好么？我很好!但 我还没吃')
        self.assertLessEqual(d.id, ctypes.c_uint(-1).value)
        self.assertGreaterEqual(d.id, 0)
        self.assertEqual(len(list(d.sentences)), 3)

    def test_multi_sent_doc_list(self):
        dirname = os.path.dirname(__file__)

        with open(os.path.join(dirname, 'tangshi.txt'), encoding='utf8') as fp:
            self.test_data = [v.strip() for v in fp if v.strip() and len(v.strip()) > 10]
            tmp = self.test_data
            self.test_data2 = [MultiSentDocument(t) for t in tmp]

        sents, ids = map(list, zip(*[(s, d.id) for d in self.test_data2 for s in d.sentences]))
        self.assertEqual(len(sents), len(ids))
