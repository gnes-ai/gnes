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


import numpy as np

from .base import BaseService as BS, MessageHandler, ServiceError
from ..proto import gnes_pb2, blob2array


class IndexerService(BS):
    handler = MessageHandler(BS.handler)

    def post_init(self):
        from ..indexer.base import BaseIndexer
        self._model = self.load_model(BaseIndexer)
        from ..scorer.base import BaseScorer
        self._scorer = self.load_model(BaseScorer, yaml_path=self.args.scorer_yaml_path)

    @handler.register(gnes_pb2.Request.IndexRequest)
    def _handler_index(self, msg: 'gnes_pb2.Message'):
        from ..indexer.base import BaseChunkIndexer, BaseDocIndexer
        if isinstance(self._model, BaseChunkIndexer):
            self._handler_chunk_index(msg)
        elif isinstance(self._model, BaseDocIndexer):
            self._handler_doc_index(msg)
        else:
            raise ServiceError(
                'unsupported indexer, dont know how to use %s to handle this message' % self._model.__bases__)
        msg.response.index.status = gnes_pb2.Response.SUCCESS
        self.is_model_changed.set()

    def _handler_chunk_index(self, msg: 'gnes_pb2.Message'):
        vecs, doc_ids, offsets, weights = [], [], [], []

        for d in msg.request.index.docs:
            if not d.chunks:
                raise ServiceError('document contains no chunks! doc: %s' % d)
            else:
                vecs += [blob2array(c.embedding) for c in d.chunks]
                doc_ids += [d.doc_id] * len(d.chunks)
                offsets += [c.offset for c in d.chunks]
                weights += [c.weight for c in d.chunks]

        self._model.add(list(zip(doc_ids, offsets)), np.concatenate(vecs, 0), weights)

    def _handler_doc_index(self, msg: 'gnes_pb2.Message'):
        self._model.add([d.doc_id for d in msg.request.index.docs],
                        [d for d in msg.request.index.docs],
                        [d.weight for d in msg.request.index.docs])

    @handler.register(gnes_pb2.Request.QueryRequest)
    def _handler_chunk_search(self, msg: 'gnes_pb2.Message'):
        from ..indexer.base import BaseChunkIndexer
        if not isinstance(self._model, BaseChunkIndexer):
            raise ServiceError(
                'unsupported indexer, dont know how to use %s to handle this message' % self._model.__bases__)

        from ..scorer.base import BaseChunkScorer
        if not isinstance(self._scorer, BaseChunkScorer):
            raise ServiceError(
                'unsupported scorer, dont know how to use %s to handle this message' % self._scorer.__bases__)

        vecs = [blob2array(c.embedding) for c in msg.request.search.query.chunks]
        topk = msg.request.search.top_k
        results = self._model.query(np.concatenate(vecs, 0), top_k=msg.request.search.top_k)

        for q_chunk, topk_chunks in zip(msg.request.search.query.chunks, results):
            for _doc_id, _offset, _weight, _relevance in topk_chunks:
                r = msg.response.search.topk_results.add()
                r.chunk.doc_id = _doc_id
                r.chunk.offset = _offset
                r.chunk.weight = _weight
                r.score = self._scorer.compute(q_chunk, r.chunk, _relevance)

        msg.response.search.top_k = topk

    @handler.register(gnes_pb2.Response.QueryResponse)
    def _handler_doc_search(self, msg: 'gnes_pb2.Message'):
        # if msg.response.search.level != gnes_pb2.Response.QueryResponse.DOCUMENT_NOT_FILLED:
        #     raise ServiceError('dont know how to handle QueryResponse at %s level' % msg.response.search.level)
        from ..indexer.base import BaseDocIndexer
        if not isinstance(self._model, BaseDocIndexer):
            raise ServiceError(
                'unsupported indexer, dont know how to use %s to handle this message' % self._model.__bases__)

        from ..scorer.base import BaseDocScorer
        if not isinstance(self._scorer, BaseDocScorer):
            raise ServiceError(
                'unsupported scorer, dont know how to use %s to handle this message' % self._scorer.__bases__)

        doc_ids = [r.doc.doc_id for r in msg.response.search.topk_results]
        docs = self._model.query(doc_ids)
        for r, d in zip(msg.response.search.topk_results, docs):
            if d is not None:
                # fill in the doc if this shard returns non-empty
                r.doc.CopyFrom(d)
                r.score = self._scorer.compute(d)

        # msg.response.search.level = gnes_pb2.Response.QueryResponse.DOCUMENT
