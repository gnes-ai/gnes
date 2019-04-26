#  Copyright 2019
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import pickle
from threading import Thread, Event
from typing import List, Any

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

    def add(self, keys: List[int], docs: List[Any], *args, **kwargs):
        with self._db.write_batch() as wb:
            for k, d in zip(keys, docs):
                doc_id = pickle.dumps(k)
                doc = pickle.dumps(d)
                wb.put(doc_id, doc)

    def query(self, keys: List[int], top_k: int = 1, *args, **kwargs) -> List[Any]:
        res = []
        for k in keys:
            doc_id = pickle.dumps(k)
            v = self._db.get(doc_id)
            res.append(pickle.loads(v) if v else self._NOT_FOUND)
        return res

    def close(self):
        super().close()
        self._db.close()


class AsyncLVDBIndexer(LVDBIndexer):
    def __init__(self, data_path: str, *args, **kwargs):
        super().__init__(data_path, *args, **kwargs)
        self._is_listening = Event()
        self._is_listening.set()
        self._is_idle = Event()
        self._is_idle.set()
        self._jobs = []
        self._thread = Thread(target=self._db_write)
        self._thread.setDaemon(1)
        self._thread.start()

    def add(self, keys: List[int], docs: List[BaseDocument], *args, **kwargs):
        self._jobs.append((keys, docs))

    def query(self, keys: List[int], top_k: int = 1, *args, **kwargs) -> List[Any]:
        self._is_idle.wait()
        return super().query(keys, top_k)

    def _db_write(self):
        while self._is_listening.is_set():
            while self._jobs:
                self._is_idle.clear()
                keys, docs = self._jobs.pop()
                super().add(keys, docs)
            self._is_idle.set()

    def __getstate__(self):
        d = super().__getstate__()
        del d['_thread']
        del d['_is_busy']
        del d['_is_listening']
        return d

    def __setstate__(self, d):
        super().__setstate__(d)
        self._is_listening = Event()
        self._is_listening.set()
        self._is_idle = Event()
        self._is_idle.set()
        self._thread = Thread(target=self._db_write)
        self._thread.setDaemon(1)
        self._thread.start()
        self._jobs = []

    def close(self):
        self._jobs.clear()
        self._is_listening.clear()
        self._is_idle.wait()
        self._thread.join()
        super().close()
