import os
import unittest
from shutil import rmtree

from gnes.indexer.fulltext.filesys import DirectoryIndexer
from gnes.preprocessor.base import BasePreprocessor
from gnes.proto import gnes_pb2


class TestDictIndexer(unittest.TestCase):
    def setUp(self):
        self.dirname = os.path.dirname(__file__)

        self.video_path = os.path.join(self.dirname, 'videos')
        self.video_bytes = [open(os.path.join(self.video_path, _), 'rb').read()
                            for _ in os.listdir(self.video_path)]

        self.pipeline_name = 'pipe-gif'
        self.pipeline_yml_path = os.path.join(self.dirname, 'yaml/%s.yml' % self.pipeline_name)
        self.data_path = './test_chunkleveldb'
        self.dump_path = os.path.join(self.dirname, 'indexer.bin')

    def tearDown(self):
        if os.path.exists(self.data_path):
            rmtree(self.data_path)

    def init_db(self):
        self.db = DirectoryIndexer(self.data_path)

        self.d = gnes_pb2.Document()
        self.d.doc_id = 0
        self.d.raw_bytes = self.video_bytes[0]

        preprocess = BasePreprocessor.load_yaml(self.pipeline_yml_path)
        preprocess.apply(self.d)

        self.db.add(list(range(len(self.video_bytes))), [self.d])

    def test_add_docs(self):
        self.init_db()
        self.assertTrue(os.path.exists(os.path.join(self.data_path, str(self.d.doc_id))))
        self.assertEqual(len(self.d.chunks), len(os.listdir(os.path.join(self.data_path, str(self.d.doc_id)))))

    def test_query_docs(self):
        self.init_db()

        query_list = [0, 1, 2]
        res = self.db.query(query_list)
        num_non_empty = sum(1 for d in res if d)
        self.assertEqual(num_non_empty, 1)
