import unittest
from src.nes.indexer.leveldb import BaseLVDB
import random
import os
from shutil import rmtree


class TestBaseLVDB(unittest.TestCase):
    def setUp(self):
        self.doc_ids = [bytes(str(random.random()), 'utf8')
                        for _ in range(100)]
        self.contents = [bytes('中文abc {}'.format(random.random()), 'utf8')
                         for _ in range(100)]

        query_ids_in = self.doc_ids[:10]
        query_ids_out = [bytes(str(random.random()), 'utf8')
                         for _ in range(10)]
        query_ids_out = [q for q in query_ids_out if q not in self.doc_ids]

        self.query_ids = query_ids_in + query_ids_out

        self.db_path = './test_leveldb'

    def tearDown(self):
        if os.path.exists(self.db_path):
            rmtree(self.db_path)

    def test_add(self):
        db = BaseLVDB(self.db_path)
        db.add(self.doc_ids, self.contents)
        self.assertTrue(os.path.exists(self.db_path))

    def test_query(self):
        db = BaseLVDB(self.db_path)
        db.add(self.doc_ids, self.contents)
        res = db.query(self.query_ids)

        self.assertEqual(10,
                         sum([res[i] == self.contents[i] for i in range(10)]))
        self.assertEqual(len(self.query_ids) - 10,
                         sum([qi is None for qi in res[10:]]))
