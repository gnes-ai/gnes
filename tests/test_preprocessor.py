import os
import unittest

from gnes.preprocessor.text import line2pb_doc, txt_file2pb_docs
from gnes.proto import gnes_pb2


class TestProto(unittest.TestCase):

    def setUp(self):
        self.single_cn = '矫矫珍木巅，得无金丸惧。'
        self.single_en = 'When forty winters shall besiege thy brow. And dig deep trenches in thy beautys field.'
        self.dirname = os.path.dirname(__file__)

    def test_single_doc(self):
        print(line2pb_doc(self.single_cn))
        print(line2pb_doc(self.single_en))

    def test_cn_file_doc(self):
        with open(os.path.join(self.dirname, '26-doc-chinese.txt'), 'r', encoding='utf8') as fp:
            self.assertEqual(len(txt_file2pb_docs(fp, 0)), 26)

    def test_en_file_doc(self):
        with open(os.path.join(self.dirname, '6-doc-english.txt'), 'r', encoding='utf8') as fp:
            self.assertEqual(len(txt_file2pb_docs(fp, 0)), 6)

    def test_request(self):
        with open(os.path.join(self.dirname, '26-doc-chinese.txt'), 'r', encoding='utf8') as fp:
            docs = txt_file2pb_docs(fp, 0)
        r = gnes_pb2.Request()
        r.train.docs.extend(docs)
        self.assertEqual(len(r.train.docs), 26)
