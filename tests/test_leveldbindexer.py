import os
import random
import unittest
from shutil import rmtree

from gnes.document import UniSentDocument, MultiSentDocument, DocumentMapper
from gnes.indexer.leveldb import LVDBIndexer


class TestBaseLVDB(unittest.TestCase):
    def setUp(self):
        dirname = os.path.dirname(__file__)

        self.test_data1 = DocumentMapper(UniSentDocument.from_file(os.path.join(dirname, 'tangshi.txt')))
        self.test_data2 = DocumentMapper(MultiSentDocument.from_file(os.path.join(dirname, 'tangshi.txt')))

        self.query_hit_id = self.test_data1.doc_id_document[0]
        self.query_miss_id = [random.randint(0, 10000) for _ in self.test_data1.doc_id_document[0]]

        self.db_path = './test_leveldb'
        self.dump_path = os.path.join(dirname, 'indexer.bin')

    def tearDown(self):
        if os.path.exists(self.db_path):
            rmtree(self.db_path)

    def test_add_uni(self):
        db = LVDBIndexer(self.db_path)
        db.add(*self.test_data1.doc_id_document)
        self.assertTrue(os.path.exists(self.db_path))
        self.assertLess(0, len(os.listdir(self.db_path)))
        db.close()

    def test_add_multi(self):
        db = LVDBIndexer(self.db_path)
        db.add(*self.test_data2.doc_id_document)
        self.assertTrue(os.path.exists(self.db_path))
        self.assertLess(0, len(os.listdir(self.db_path)))
        db.close()

    def test_query(self):
        db = LVDBIndexer(self.db_path)
        db.add(*self.test_data1.doc_id_document)
        res1 = db.query(self.query_hit_id)
        num_non_empty = sum(1 for d in res1 if d)
        self.assertEqual(num_non_empty, self.test_data1.length)

        res2 = db.query(self.query_miss_id)
        num_non_empty = sum(1 for d in res2 if d)
        self.assertEqual(num_non_empty, 0)
        db.close()

    def dump_load(self):
        tmp = LVDBIndexer(self.db_path)
        tmp.add(*self.test_data1.doc_id_document)
        tmp.dump(self.dump_path)
        tmp.close()

        db = LVDBIndexer.load(self.db_path)
        res1 = db.query(self.query_hit_id)
        num_non_empty = sum(1 for d in res1 if d)
        self.assertEqual(num_non_empty, self.test_data1.length)

        res2 = db.query(self.query_miss_id)
        num_non_empty = sum(1 for d in res2 if d)
        self.assertEqual(num_non_empty, 0)
        db.close()
