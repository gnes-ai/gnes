import unittest
from src.nes.indexer import BaseTextIndexer
from src.nes.document import UniSentDocument, MultiSentDocument
import os
from shutil import rmtree


class TestBaseTextIndexer(unittest.TestCase):
    def setUp(self):
        self.corpus = ['你好么？我很好',
                       '早上好？我的伙伴',
                       '人生若之如初见，何事西风悲画扇']
        self.docs = []
        for line in self.corpus:
            self.docs.append(UniSentDocument(line))
            self.docs.append(MultiSentDocument(line))
        self.db_path = './test_base_text_indexer'

    def tearDown(self):
        if os.path.exists(self.db_path):
            rmtree(self.db_path)

    def test_add(self):
        db = BaseTextIndexer(self.db_path)
        db.add(self.docs)
        self.assertTrue(os.path.exists(self.db_path))
        self.assertLess(0, len(os.listdir(self.db_path)))

    def test_query(self):
        db = BaseTextIndexer(self.db_path)
        db.add(self.docs)
        res = db.query([doc._id for doc in self.docs])
        comp = [res[i]['content'] == self.docs[i]._content
                for i in range(len(res))]
        self.assertEqual(len(res), sum(comp))
        # return {} if doc_id not in database
        self.assertFalse(db.query([-1])[0])
