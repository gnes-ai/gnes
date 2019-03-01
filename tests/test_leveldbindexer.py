import os
import random
import unittest
from shutil import rmtree

from src.nes.document import UniSentDocument, MultiSentDocument
from src.nes.indexer.leveldb import LVDBIndexer


class TestBaseLVDB(unittest.TestCase):
    def setUp(self):
        dirname = os.path.dirname(__file__)

        with open(os.path.join(dirname, 'tangshi.txt'), encoding='utf8') as fp:
            tmp = [v.strip() for v in fp if v.strip() and len(v.strip()) > 10]
            self.test_data1 = [UniSentDocument(t) for t in tmp]
            self.test_data2 = [MultiSentDocument(t) for t in tmp]
            self.query_hit_id = [d.id for d in self.test_data1]
            self.query_miss_id = [random.randint(0, 10000) for _ in self.test_data1]

        self.db_path = './test_leveldb'

    def tearDown(self):
        if os.path.exists(self.db_path):
            rmtree(self.db_path)

    def test_add_uni(self):
        db = LVDBIndexer(self.db_path)
        db.add(self.test_data1)
        self.assertTrue(os.path.exists(self.db_path))
        self.assertLess(0, len(os.listdir(self.db_path)))
        db.close()

    def test_add_multi(self):
        db = LVDBIndexer(self.db_path)
        db.add(self.test_data2)
        self.assertTrue(os.path.exists(self.db_path))
        self.assertLess(0, len(os.listdir(self.db_path)))
        db.close()

    def test_query(self):
        db = LVDBIndexer(self.db_path)
        db.add(self.test_data1)
        res1 = db.query(self.query_hit_id)
        num_non_empty = sum(1 for d in res1 if d)
        self.assertEqual(num_non_empty, len(self.test_data1))

        res2 = db.query(self.query_miss_id)
        num_non_empty = sum(1 for d in res2 if d)
        self.assertEqual(num_non_empty, 0)
        db.close()
