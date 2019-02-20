import ctypes
import unittest

from src.nes.document import UniSentDocument, MultiSentDocument


class TestIndexer(unittest.TestCase):
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
