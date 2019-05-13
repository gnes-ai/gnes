import os
import unittest
from shutil import rmtree

from gnes.indexer.leveldb import AsyncLVDBIndexer
from gnes.proto import gnes_pb2


class TestBaseLVDB(unittest.TestCase):
    def setUp(self):
        dirname = os.path.dirname(__file__)

        self.test_docs = []
        with open(os.path.join(dirname, 'tangshi.txt')) as f:
            title = ''
            sents = []
            doc_id = 0
            for line in f:
                line = line.strip()

                if line and not title:
                    title = line
                    sents.append(line)
                elif line and title:
                    sents.append(line)
                elif not line and title and len(sents) > 1:
                    doc = gnes_pb2.Document()
                    doc.id = doc_id
                    doc.text = ' '.join(sents)
                    doc.text_chunks.extend(sents)
                    doc.doc_size = len(sents)

                    doc.is_parsed = True
                    doc.is_encoded = True
                    doc_id += 1
                    sents.clear()
                    title = ''
                    self.test_docs.append(doc)

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
