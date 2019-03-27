import ctypes
import os
import unittest

from gnes.document import UniSentDocument, MultiSentDocument
from gnes.helper import batch_iterator


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

    def test_from_file(self):
        dirname = os.path.dirname(__file__)
        docs1 = UniSentDocument.from_file(os.path.join(dirname, 'tangshi.txt'))
        docs2 = MultiSentDocument.from_file(os.path.join(dirname, 'tangshi.txt'))
        self.assertEqual(len(list(docs1)), len(list(docs2)))

    def test_batching(self):
        dirname = os.path.dirname(__file__)
        docs1 = UniSentDocument.from_file(os.path.join(dirname, 'tangshi.txt'))
        batch_size = 5
        for b in batch_iterator(docs1, batch_size):
            self.assertLessEqual(len(b), batch_size)

        docs1 = UniSentDocument.from_file(os.path.join(dirname, 'tangshi.txt'))
        batch_size = 4096
        j = 0
        for b in batch_iterator(docs1, batch_size):
            self.assertLessEqual(len(b), batch_size)
            j += 1
        self.assertEqual(j, 1)

    def test_broken_file(self):
        a = ['我我我我我我我我\n', '我我我我。我我我我\n', '我我\n']
        with open('tmp.txt', 'w', encoding='utf8') as fp:
            fp.writelines(a)
        docs1 = UniSentDocument.from_file('tmp.txt')
        docs2 = MultiSentDocument.from_file('tmp.txt')
        self.assertEqual(len(docs1), 3)
        self.assertEqual(len(docs2), 2)
        docs1 = UniSentDocument.from_file('tmp.txt', min_len_seq=3)
        self.assertEqual(len(docs1), 2)
