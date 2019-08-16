import os
import unittest

from gnes.preprocessor.base import BasePreprocessor, PipelinePreprocessor
from gnes.proto import gnes_pb2


class P1(BasePreprocessor):
    def apply(self, doc: 'gnes_pb2.Document'):
        doc.doc_id += 1


class P2(BasePreprocessor):
    def apply(self, doc: 'gnes_pb2.Document'):
        doc.doc_id *= 3


class TestPartition(unittest.TestCase):
    def setUp(self):
        self.dirname = os.path.dirname(__file__)
        self.p3_name = 'pipe-p12'
        self.yml_dump_path = os.path.join(self.dirname, '%s.yml' % self.p3_name)
        self.bin_dump_path = os.path.join(self.dirname, '%s.bin' % self.p3_name)

    def tearDown(self):
        if os.path.exists(self.yml_dump_path):
            os.remove(self.yml_dump_path)
        if os.path.exists(self.bin_dump_path):
            os.remove(self.bin_dump_path)

    def test_pipelinepreproces(self):
        p3 = PipelinePreprocessor()
        p3.components = lambda: [P1(), P2()]
        d = gnes_pb2.Document()
        d.doc_id = 1
        p3.apply(d)
        self.assertEqual(d.doc_id, 6)

        p3.name = self.p3_name
        p3.dump_yaml()
        p3.dump()

        p4 = BasePreprocessor.load_yaml(p3.yaml_full_path)
        p4.apply(d)
        self.assertEqual(d.doc_id, 21)
