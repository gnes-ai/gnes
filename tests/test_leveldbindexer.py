import os
import unittest
from shutil import rmtree

from gnes.indexer.leveldb import LVDBIndexer
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

        # self.query_hit_id = self.test_data1.doc_id_document[0]
        # self.query_miss_id = [random.randint(0, 10000) for _ in self.test_data1.doc_id_document[0]]

        self.db_path = './test_leveldb'
        self.dump_path = os.path.join(dirname, 'indexer.bin')

    def tearDown(self):
        if os.path.exists(self.db_path):
            rmtree(self.db_path)

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

        res2 = db.query(range(len(self.test_docs)+1, len(self.test_docs)+100))
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

        res2 = db.query(range(len(self.test_docs)+1, len(self.test_docs)+100))
        num_non_empty = sum(1 for d in res2 if d)
        self.assertEqual(num_non_empty, 0)
        db.close()
