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


import os
from typing import List

from ..base import BaseDocIndexer as BDI
from ...proto import gnes_pb2


class DirectoryIndexer(BDI):

    def __init__(self, data_path: str,
                 keep_na_doc: bool = True,
                 file_suffix: str = 'gif',
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_path = data_path
        self.file_suffix = file_suffix
        self.keep_na_doc = keep_na_doc
        self._NOT_FOUND = None

    @BDI.update_counter
    def add(self, keys: List[int], docs: List['gnes_pb2.Document'], *args, **kwargs):
        """
        write GIFs of each document into disk
        folder structure: /data_path/doc_id/0.gif, 1.gif...
        :param keys: list of doc id
        :param docs: list of docs
        """
        for k, d in zip(keys, docs):
            dirs = os.path.join(self.data_path, str(k))
            if not os.path.exists(dirs):
                os.makedirs(dirs)
            # keep doc meta in .meta file
            with open(os.path.join(dirs, '.meta'), 'wb') as f:
                f.write(d.meta_info or b'')

            for i, chunk in enumerate(d.chunks):
                with open(os.path.join(dirs, '%d.%s' % (i, self.file_suffix)), 'wb') as f:
                    f.write(chunk.raw)

    def query(self, keys: List[int], *args, **kwargs) -> List['gnes_pb2.Document']:
        """
        :param keys: list of doc id
        :return: list of documents whose chunks field contain all the GIFs of this doc(one GIF per chunk)
        """
        res = []
        for k in keys:
            doc = gnes_pb2.Document()
            target_dirs = os.path.join(self.data_path, str(k))

            if not os.path.exists(target_dirs):
                if self.keep_na_doc:
                    res.append(self._NOT_FOUND)
            else:
                with open(os.path.join(target_dirs, '.meta'), 'rb') as f:
                    doc.meta_info = f.read()
                for raw_file in os.listdir(target_dirs):
                    if not os.path.isdir(raw_file):
                        c = doc.chunks.add()
                        c.doc_id = k
                        with open(os.path.join(target_dirs, raw_file), 'rb') as raw:
                            c.raw = raw.read()
                res.append(doc)
        return res

