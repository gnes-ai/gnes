#  Tencent is pleased to support the open source community by making GNES available.
#
#  Copyright (C) 2019 THL A29 Limited, a Tencent company. All rights reserved.
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

# pylint: disable=low-comment-ratio


import pickle
from threading import Thread, Event
from typing import List, Any

from ..base import BaseTextIndexer
from ...proto import gnes_pb2


class LVDBIndexer(BaseTextIndexer):

    def __init__(self, data_path: str, keep_na_doc: bool = True, *args, **kwargs):
        super().__init__()
        self.data_path = data_path
        self.keep_na_doc = keep_na_doc
        self._NOT_FOUND = None

    def post_init(self):
        import plyvel
        self._db = plyvel.DB(self.data_path, create_if_missing=True)

    def add(self, keys: List[int], docs: List['gnes_pb2.Document'], *args, **kwargs):
        with self._db.write_batch() as wb:
            for k, d in zip(keys, docs):
                doc_id = pickle.dumps(k)
                doc = d.SerializeToString()
                wb.put(doc_id, doc)

    def query(self, keys: List[int], *args, **kwargs) -> List['gnes_pb2.Document']:
        res = []
        for k in keys:
            doc_id = pickle.dumps(k)
            v = self._db.get(doc_id)
            doc = gnes_pb2.Document()
            if v is not None:
                doc.ParseFromString(v)
                res.append(doc)
            elif self.keep_na_doc:
                res.append(self._NOT_FOUND)
        return res

    def close(self):
        super().close()
        self._db.close()


class AsyncLVDBIndexer(LVDBIndexer):
    def post_init(self):
        super().post_init()
        self._is_listening = Event()
        self._is_listening.set()
        self._is_idle = Event()
        self._is_idle.set()
        self._jobs = []
        self._thread = Thread(target=self._db_write)
        self._thread.setDaemon(1)
        self._thread.start()

    def add(self, keys: List[int], docs: List['gnes_pb2.Document'], *args, **kwargs):
        self._jobs.append((keys, docs))

    def query(self, *args, **kwargs) -> List[Any]:
        self._is_idle.wait()
        return super().query(*args, **kwargs)

    def _db_write(self):
        while self._is_listening.is_set():
            while self._jobs:
                self._is_idle.clear()
                keys, docs = self._jobs.pop()
                super().add(keys, docs)
            self._is_idle.set()

    def close(self):
        self._jobs.clear()
        self._is_listening.clear()
        self._is_idle.wait()
        self._thread.join()
        super().close()
