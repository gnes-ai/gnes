import os
import unittest
from shutil import rmtree

from gnes.indexer.doc.leveldb import AsyncLVDBIndexer
from tests import txt_file2pb_docs


class TestBaseLVDB(unittest.TestCase):
    def setUp(self):
        dirname = os.path.dirname(__file__)

        self.test_docs = txt_file2pb_docs(open(os.path.join(dirname, 'tangshi.txt')))

        self.query_hit_id = list(range(len(self.test_docs)))
        self.query_miss_id = list(range(len(self.test_docs) + 1, len(self.test_docs) + 100))

        self.db_path = './test_leveldb'
        self.dump_path = os.path.join(dirname, 'indexer.bin')

    def tearDown(self):
        if os.path.exists(self.db_path):
            rmtree(self.db_path)

    def test_add_uni(self):
        db = AsyncLVDBIndexer(self.db_path)
        db.add(range(len(self.test_docs)), self.test_docs)
        self.assertTrue(os.path.exists(self.db_path))
        self.assertLess(0, len(os.listdir(self.db_path)))
        db.close()

    def test_add_multi(self):
        db = AsyncLVDBIndexer(self.db_path)
        db.add(range(len(self.test_docs)), self.test_docs)
        self.assertTrue(os.path.exists(self.db_path))
        self.assertLess(0, len(os.listdir(self.db_path)))
        db.close()

    @unittest.SkipTest
    def test_query(self):
        db = AsyncLVDBIndexer(self.db_path)
        db.add(range(len(self.test_docs)), self.test_docs)
        res1 = db.query(self.query_hit_id)
        num_non_empty = sum(1 for d in res1 if d)
        self.assertEqual(num_non_empty, len(self.test_docs))

        res2 = db.query(self.query_miss_id)
        num_non_empty = sum(1 for d in res2 if d)
        self.assertEqual(num_non_empty, 0)
        db.close()

    def dump_load(self):
        tmp = AsyncLVDBIndexer(self.db_path)
        tmp.add(range(len(self.test_docs)), self.test_docs)
        tmp.dump(self.dump_path)
        tmp.close()

        db = AsyncLVDBIndexer.load(self.db_path)
        res1 = db.query(self.query_hit_id)
        num_non_empty = sum(1 for d in res1 if d)
        self.assertEqual(num_non_empty, len(self.test_docs))

        res2 = db.query(self.query_miss_id)
        num_non_empty = sum(1 for d in res2 if d)
        self.assertEqual(num_non_empty, 0)
        db.close()
