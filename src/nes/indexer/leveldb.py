import json
from typing import List, Dict, Any
from threading import Thread
import plyvel
import time

from . import BaseTextIndexer
from ..document import BaseDocument


class LVDBIndexer(BaseTextIndexer):
    def __init__(self, data_path: str):
        super().__init__()
        self._db = plyvel.DB(data_path, create_if_missing=True)
        self._NOT_FOUND = {}
        self.thread_pool = []

    def add(self, docs: List[BaseDocument]):
        for thread in self.thread_pool:
            if not thread.is_alive():
                self.thread_pool.remove(thread)

        if len(self.thread_pool) < 10:
            thread = Thread(target=self._add,
                            args=(docs,), kwargs=None)
            thread.start()
            self.thread_pool.append(thread)
        else:
            time.sleep(1)
            self.add(docs)

    def _add(self, docs: List[BaseDocument]):
        with self._db.write_batch() as wb:
            for d in docs:
                doc_id = self._int2bytes(d.id)
                doc = self._doc2bytes(d)
                wb.put(doc_id, doc)

    def query(self, keys: List[int]) -> List[Dict[str, Any]]:
        self._check_thread()
        res = []
        for k in keys:
            doc_id = self._int2bytes(k)
            v = self._db.get(doc_id)
            res.append(self._bytes2doc(v) if v else self._NOT_FOUND)
        return res

    def _check_thread(self):
        if self.thread_pool:
            for thread in self.thread_pool:
                thread.join()
            self.thread_pool = []

    @staticmethod
    def _doc2bytes(doc: BaseDocument):
        # doc._sentences is iterator, which can't be dumped.
        return bytes(json.dumps({
            'id': doc.id,
            'sentences': list(doc.sentences),
            'content': doc._content},
            ensure_ascii=False), 'utf8')

    @staticmethod
    def _bytes2doc(content):
        if content:
            return json.loads(content.decode())
        else:
            return {}

    @staticmethod
    def _int2bytes(x):
        return x.to_bytes((x.bit_length() + 7) // 8, 'big')

    @staticmethod
    def _bytes2int(xbytes):
        return int.from_bytes(xbytes, 'big')
