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

import numpy as np

from .base import BaseService as BS, ComponentNotLoad, MessageHandler
from ..proto import gnes_pb2, blob2array


class IndexerService(BS):
    handler = MessageHandler(BS.handler)

    def _post_init(self):
        from ..indexer.base import BaseIndexer

        self._model = None
        try:
            self._model = BaseIndexer.load(self.args.dump_path)
            self.logger.info('load an indexer')
        except FileNotFoundError:
            try:
                self._model = BaseIndexer.load_yaml(
                    self.args.yaml_path)
                self.logger.warining(
                    'load an uninitialized indexer, indexing is needed!')
            except FileNotFoundError:
                raise ComponentNotLoad

    @handler.register(gnes_pb2.Request.IndexRequest)
    def _handler_index(self, msg: 'gnes_pb2.Message'):
        all_vecs = []
        doc_ids = []
        offsets = []
        weights = []

        for d in msg.request.index.docs:
            all_vecs.append(blob2array(d.chunk_embeddings))
            doc_ids += [d.doc_id] * len(d.chunks)
            offsets += [c.offset_1d for c in d.chunks]
            weights += [c.weight for c in d.chunks]

        from ..indexer.base import BaseVectorIndexer, BaseTextIndexer
        if isinstance(self._model, BaseVectorIndexer):
            self._model.add(list(zip(doc_ids, offsets)), np.concatenate(all_vecs, 0), weights)

        if isinstance(self._model, BaseTextIndexer):
            self._model.add([d.doc_id for d in msg.request.index.docs], [d for d in msg.request.index.docs])

        msg.response.index.status = gnes_pb2.Response.SUCCESS
        self.is_model_changed.set()

    @handler.register(gnes_pb2.Request.QueryRequest)
    def _handler_search(self, msg: 'gnes_pb2.Message'):
        vecs = blob2array(msg.request.search.query.chunk_embeddings)
        results = self._model.query(vecs, top_k=msg.request.search.top_k)
        for all_topks in results:
            r_topk = msg.response.search.result.add()
            for _doc_id, _offset, _score, _weight in all_topks:
                r = r_topk.topk_results.add()
                r.chunk.doc_id = _doc_id
                r.chunk.offset_1d = _offset
                r.chunk.weight = _weight
                r.chunk.relevance = _score