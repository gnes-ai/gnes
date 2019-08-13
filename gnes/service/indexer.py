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

    @handler.register(gnes_pb2.Request.IndexRequest)
    def _handler_index(self, msg: 'gnes_pb2.Message'):
        all_vecs = []
        doc_ids = []
        offsets = []
        weights = []

        for d in msg.request.index.docs:
            if len(d.chunks):
                all_vecs.append(blob2array(d.chunk_embeddings))
                doc_ids += [d.doc_id] * len(d.chunks)
                if d.doc_type == gnes_pb2.Document.TEXT:
                    offsets += [c.offset_1d for c in d.chunks]
                elif d.doc_type == gnes_pb2.Document.IMAGE:
                    offsets += [c.offset_nd for c in d.chunks]
                elif d.doc_type == gnes_pb2.Document.VIDEO:
                    offsets += [c.offset_1d for c in d.chunks]
                elif d.doc_type == gnes_pb2.Document.AUDIO:
                    offsets += [c.offset_1d for c in d.chunks]
                weights += [c.weight for c in d.chunks]

        from ..indexer.base import BaseVectorIndexer, BaseTextIndexer
        if isinstance(self._model, BaseVectorIndexer):
            self._model.add(list(zip(doc_ids, offsets)),
                            np.concatenate(all_vecs, 0),
                            weights)
        elif isinstance(self._model, BaseTextIndexer):
            self._model.add([d.doc_id for d in msg.request.index.docs],
                            [d for d in msg.request.index.docs],
                            [d.weight for d in msg.request.index.docs])

        msg.response.index.status = gnes_pb2.Response.SUCCESS
        self.is_model_changed.set()

    @handler.register(gnes_pb2.Request.QueryRequest)
    def _handler_chunk_search(self, msg: 'gnes_pb2.Message'):
        def _cal_offset_relevance(q_offset, i_offset):
            import math
            if not isinstance(q_offset, list) and isinstance(i_offset, list):
                raise TypeError("Type of qc_offset and offset is supposed to be (list, list), "
                                "but actually we got (%s, %s)" % (str(type(q_offset)), str(type(i_offset))))
            if not len(q_offset) == 2 and len(i_offset) == 2:
                raise ValueError("Length of qc_offset and offset should be (2, 2), "
                                 "but actually we got (%d, %d)" % (len(q_offset), len(i_offset)))
            return 1 / (1 + math.sqrt((q_offset[0] - i_offset[0]) ** 2 + (q_offset[1] - i_offset[1]) ** 2))

        vecs = blob2array(msg.request.search.query.chunk_embeddings)
        q_offset = [c.offset_nd if msg.request.search.query.doc_type == 'IMAGE'
                    else c.offset_1d for c in msg.request.search.query.chunks]
        topk = msg.request.search.top_k
        results = self._model.query(vecs, top_k=msg.request.search.top_k)
        q_weights = [qc.weight for qc in msg.request.search.query.chunks]
        for all_topks, qc_weight, qc_offset in zip(results, q_weights, q_offset):
            for _doc_id, _offset, _weight, _relevance in all_topks:
                r = msg.response.search.topk_results.add()
                r.chunk.doc_id = _doc_id
                r.chunk.weight = _weight
                if msg.request.search.query.doc_type == 'IMAGE':
                    r.chunk.offset_nd = _offset
                    offset_relevance = _cal_offset_relevance(qc_offset, _offset)
                else:
                    r.chunk.offset_1d = _offset
                    offset_relevance = 1
                r.score = _weight * qc_weight * _relevance * offset_relevance
                r.score_explained = '[chunk_score at doc: %d, offset: %d] = ' \
                                    '(doc_chunk_weight: %.6f) * ' \
                                    '(query_doc_chunk_relevance: %.6f) * ' \
                                    '(query_doc_offset_relevance: %.6f) * ' \
                                    '(query_chunk_weight: %.6f)' % (
                                        _doc_id, _offset, _weight, _relevance, offset_relevance, qc_weight)
            msg.response.search.top_k = topk

    @handler.register(gnes_pb2.Response.QueryResponse)
    def _handler_doc_search(self, msg: 'gnes_pb2.Message'):
        if msg.response.search.level == gnes_pb2.Response.QueryResponse.DOCUMENT_NOT_FILLED:
            doc_ids = [r.doc.doc_id for r in msg.response.search.topk_results]
            docs = self._model.query(doc_ids)
            for r, d in zip(msg.response.search.topk_results, docs):
                if d is not None:
                    # fill in the doc if this shard returns non-empty
                    r.doc.CopyFrom(d)
                    r.score *= d.weight
                    r.score_explained = '{%s} * [doc: %d] (doc_weight: %.6f)' % (
                        r.score_explained, d.doc_id, d.weight)
            msg.response.search.level = gnes_pb2.Response.QueryResponse.DOCUMENT
        else:
            raise ServiceError('i dont know how to handle QueryResponse with %s level' % msg.response.search.level)
