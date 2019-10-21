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


import gc
import pickle
from typing import List, Any

from ..base import BaseDocIndexer as BDI
from ...proto import gnes_pb2


class RocksDBIndexer(BDI):

    def __init__(self, data_path: str,
                 drop_raw_data: bool = False,
                 drop_chunk_blob: bool = False,
                 read_only: bool = False,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_path = data_path
        self.drop_raw_data = drop_raw_data
        self.drop_chunk_blob = drop_chunk_blob
        self.read_only = read_only
        self.kwargs = kwargs

    def post_init(self):
        import rocksdb
        
        opts = rocksdb.Options()
        opts.create_if_missing = True
        opts.max_open_files = 300000
        opts.write_buffer_size = 67108864
        opts.max_write_buffer_number = 3
        opts.target_file_size_base = 67108864

        opts.table_factory = rocksdb.BlockBasedTableFactory(
            filter_policy=rocksdb.BloomFilterPolicy(10),
            block_cache=rocksdb.LRUCache(2 * (1024 ** 3)),
            block_cache_compressed=rocksdb.LRUCache(500 * (1024 ** 2)))

        for key, value in self.kwargs.items():
            setattr(opts, key, value)

        self._db = rocksdb.DB(self.data_path, opts, read_only=self.read_only)


    @BDI.update_counter
    def add(self, keys: List[int], docs: List['gnes_pb2.Document'], *args, **kwargs):
        import rocksdb

        write_batch = rocksdb.WriteBatch()
        for k, d in zip(keys, docs):
            key_bytes = pickle.dumps(k)
            if self.drop_raw_data:
                d.ClearField('raw_data')
            if self.drop_chunk_blob:
                for c in d.chunks:
                    c.ClearField('blob')
            value_bytes = d.SerializeToString()
            write_batch.put(key_bytes, value_bytes)
        self._db.write(write_batch, sync=True)


    def query(self, keys: List[int], *args, **kwargs) -> List['gnes_pb2.Document']:
        query_keys = []
        for k in keys:
            key_value = pickle.dumps(k)
            query_keys.append(key_value)

        values = self._db.multi_get(query_keys)
        
        docs = []
        for k in query_keys:
            v = values[k]
            if v is not None:
                _doc = gnes_pb2.Document()
                _doc.ParseFromString(v)
                docs.append(_doc)
            else:
                docs.append(None)
        return docs


    def scan(self, reversed_scan: bool=False):
        iterator = self._db.iterkeys()

        if reversed_scan:
            iterator.seek_to_last()
        else:
            iterator.seek_to_first()

        if reversed_scan:
            iterator = reversed(iterator)
    
        for key_bytes in iterator:
            doc_id = pickle.loads(key_bytes)
            value_bytes = self._db.get(key_bytes)
            pb_doc = gnes_pb2.Document()
            pb_doc.ParseFromString(value_bytes)

            yield doc_id, pb_doc


    def close(self):
        super().close()
        try:
            del self._db
        except AttributeError:
            pass
        gc.collect()
