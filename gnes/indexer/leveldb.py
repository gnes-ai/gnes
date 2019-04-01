import json
import time
from threading import Thread
from typing import List, Dict, Any

import plyvel

from .base import BaseTextIndexer
from ..document import BaseDocument


class LVDBIndexer(BaseTextIndexer):
    def __init__(self, data_path: str, *args, **kwargs):
        super().__init__()
        self.data_path = data_path
        self._db = plyvel.DB(data_path, create_if_missing=True)
        self._NOT_FOUND = {}

    def __getstate__(self):
        d = super().__getstate__()
        del d['_db']
        return d

    def __setstate__(self, d):
        super().__setstate__(d)
        self._db = plyvel.DB(self.data_path, create_if_missing=True)

    def add(self, keys: List[int], docs: List[BaseDocument], *args, **kwargs):
        with self._db.write_batch() as wb:
            for k, d in zip(keys, docs):
                doc_id = self._int2bytes(k)
                doc = self._doc2bytes(d)
                wb.put(doc_id, doc)

    def query(self, keys: List[int], top_k: int = 1, *args, **kwargs) -> List[Dict[str, Any]]:
        res = []
        for k in keys:
            doc_id = self._int2bytes(k)
            v = self._db.get(doc_id)
            res.append(self._bytes2doc(v) if v else self._NOT_FOUND)
        return res

    def close(self):
        super().close()
        self._db.close()

    @staticmethod
    def _doc2bytes(doc: BaseDocument) -> bytes:
        # doc._sentences is iterator, which can't be dumped.
        return bytes(json.dumps({
            'id': doc.id,
            'sentences': list(doc.sentences),
            'content': doc.content},
            ensure_ascii=False), 'utf8')

    @staticmethod
    def _bytes2doc(content: bytes) -> Dict[str, Any]:
        if content:
            return json.loads(content.decode())
        else:
            return {}

    @staticmethod
    def _int2bytes(x: int) -> bytes:
        return x.to_bytes((x.bit_length() + 7) // 8, 'big')

    @staticmethod
    def _bytes2int(xbytes: bytes) -> int:
        return int.from_bytes(xbytes, 'big')


class AsyncLVDBIndexer(LVDBIndexer):
    def __init__(self, data_path: str, *args, **kwargs):
        super().__init__(data_path, *args, **kwargs)
        self._thread = Thread(target=self._db_write, args=(), kwargs=None)
        self._thread.setDaemon(1)
        self._thread.start()
        self._jobs = []
        self._db_put = False

    def add(self, keys: List[int], docs: List[BaseDocument], *args, **kwargs):
        self._jobs.append((keys, docs))

    def query(self, keys: List[int], top_k: int = 1, *args, **kwargs) -> List[Dict[str, Any]]:
        self._check_state()
        return super().query(keys, top_k)

    def _add(self, keys: List[int], docs: List[BaseDocument], *args, **kwargs):
        self._db_put = True
        super().add(keys, docs)
        self._db_put = False

    def _db_write(self):
        while True:
            time.sleep(1)
            if self._jobs:
                keys, docs = self._jobs.pop()
                self._add(keys, docs)

    def _check_state(self):
        while self._jobs or self._db_put:
            time.sleep(1)
            pass

    def __getstate__(self):
        d = super().__getstate__()
        del d['_thread']
        return d

    def __setstate__(self, d):
        super().__setstate__(d)
        self._thread = Thread(target=self._db_write, args=(), kwargs=None)
        self._thread.setDaemon(1)
        self._thread.start()

    def close(self):
        self._check_state()
        super().close()
