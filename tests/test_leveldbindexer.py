import os
import unittest
from shutil import rmtree

from gnes.indexer.doc.dict import DictIndexer
from gnes.indexer.doc.leveldb import LVDBIndexer
from gnes.proto import gnes_pb2
from tests import txt_file2pb_docs


class TestBaseLVDB(unittest.TestCase):
    def setUp(self):
        dirname = os.path.dirname(__file__)

        self.test_docs = txt_file2pb_docs(open(os.path.join(dirname, 'tangshi.txt'), encoding='utf8'))

        self.db_path = './test_leveldb'
        self.dump_path = os.path.join(dirname, 'indexer.bin')
        self.dump_yaml_path = os.path.join(dirname, 'indexer.yaml')

    def tearDown(self):
        if os.path.exists(self.db_path):
            rmtree(self.db_path)
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)
        if os.path.exists(self.dump_yaml_path):
            os.remove(self.dump_yaml_path)
        if os.path.exists('my-indexer-531.bin'):
            os.remove('my-indexer-531.bin')
        if os.path.exists('my-indexer-531.yml'):
            os.remove('my-indexer-531.yml')

    def test_dict_indexer(self):
        db = DictIndexer()
        db.add(range(len(self.test_docs)), self.test_docs)
        db.dump(self.dump_path)
        self.assertEqual(len(self.test_docs), db.num_docs)
        db2 = DictIndexer.load(self.dump_path)
        self.assertEqual(len(self.test_docs), db2.num_docs)
        db.name = 'my-indexer-531'
        db.dump()
        db.dump_yaml()
        db3 = DictIndexer.load_yaml(db.yaml_full_path)
        for k in db3.query([1, 2, 3]):
            self.assertIsInstance(k, gnes_pb2.Document)
        self.assertEqual(len(self.test_docs), db3.num_docs)

    def test_add_docs(self):
        db = LVDBIndexer(self.db_path)
        db.add(range(len(self.test_docs)), self.test_docs)
        self.assertTrue(os.path.exists(self.db_path))
        self.assertLess(0, len(os.listdir(self.db_path)))
        db.close()

    def test_query(self):
        db = LVDBIndexer(self.db_path)
        db.add(range(len(self.test_docs)), self.test_docs)

        res1 = db.query(range(len(self.test_docs)))
        num_non_empty = sum(1 for d in res1 if d)
        self.assertEqual(num_non_empty, len(self.test_docs))

        res2 = db.query(range(len(self.test_docs) + 1, len(self.test_docs) + 100))
        num_non_empty = sum(1 for d in res2 if d)
        self.assertEqual(num_non_empty, 0)
        db.close()

    def dump_load(self):
        tmp = LVDBIndexer(self.db_path)
        tmp.add(range(len(self.test_docs)), self.test_docs)
        tmp.dump(self.dump_path)
        tmp.close()

        db = LVDBIndexer.load(self.db_path)
        res1 = db.query(range(len(self.test_docs)))
        num_non_empty = sum(1 for d in res1 if d)
        self.assertEqual(num_non_empty, self.test_data1.length)

        res2 = db.query(range(len(self.test_docs) + 1, len(self.test_docs) + 100))
        num_non_empty = sum(1 for d in res2 if d)
        self.assertEqual(num_non_empty, 0)
        db.close()
