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
import zmq

from .base import BaseService as BS, ComponentNotLoad, ServiceMode, MessageHandler
from ..proto import gnes_pb2, blob2array, send_message


class IndexerService(BS):
    handler = MessageHandler(BS.handler)

    def _post_init(self):
        from ..indexer.base import BaseIndexer

        self._model = None
        try:
            self._model = BaseIndexer.load(self.args.dump_path)
            self.logger.info('load an indexer')
        except FileNotFoundError:
            if self.args.mode == ServiceMode.INDEX:
                try:
                    self._model = BaseIndexer.load_yaml(
                        self.args.yaml_path)
                    self.logger.info(
                        'load an uninitialized indexer, indexing is needed!')
                except FileNotFoundError:
                    raise ComponentNotLoad
            else:
                raise ComponentNotLoad

    def _index_and_notify(self, msg: 'gnes_pb2.Message', out: 'zmq.Socket'):
        if not msg.is_encoded:
            raise RuntimeError("the documents should be encoded at first!")

        offsets = []
        all_vecs = []
        doc_ids = []
        for doc in msg.docs:
            assert doc.doc_size == doc.encodes.shape[0]
            all_vecs.append(blob2array(doc.encodes))
            doc_ids += [doc.id] * doc.doc_size
            offsets += list(range(doc.doc_size))

        from ..indexer.base import JointIndexer, BaseBinaryIndexer, BaseTextIndexer
        if isinstance(self._model, JointIndexer) or isinstance(self._model, BaseBinaryIndexer):
            self._model.add(list(zip(doc_ids, offsets)), np.concatenate(all_vecs, 0))
        if isinstance(self._model, JointIndexer) or isinstance(self._model, BaseTextIndexer):
            self._model.add([d.id for d in msg.docs], [d for d in msg.docs])
        send_message(out, msg, self.args.timeout)
        self.is_model_changed.set()

    @handler.register(gnes_pb2.Request.IndexRequest)
    def _handler_index(self, msg: 'gnes_pb2.Message', out: 'zmq.Socket'):
        all_vecs = []
        doc_ids = []
        offsets = []

        for d in msg.request.index.docs:
            all_vecs.append(blob2array(d.chunk_embeddings))
            doc_ids += [d.doc_id] * len(d.chunks)
            offsets += [c.offset_1d for c in d.chunks]

        from ..indexer.base import JointIndexer, BaseBinaryIndexer, BaseTextIndexer
        if isinstance(self._model, JointIndexer) or isinstance(self._model, BaseBinaryIndexer):
            self._model.add(list(zip(doc_ids, offsets)), np.concatenate(all_vecs, 0))

        if isinstance(self._model, JointIndexer) or isinstance(self._model, BaseTextIndexer):
            self._model.add([d.doc_id for d in msg.request.index.docs], msg.request.index.doc)

        msg.response.index.status = gnes_pb2.Response.SUCCESS
        send_message(out, msg, self.args.timeout)
        self.is_model_changed.set()

    @handler.register(gnes_pb2.Request.QueryRequest)
    def _handler_search(self, msg: 'gnes_pb2.Message', out: 'zmq.Socket'):
        vecs = blob2array(msg.request.search.query.chunk_embeddings)
        results = self._model.query(vecs, top_k=msg.request.search.top_k)
        for q_chunk, all_topks in zip(msg.request.search.query.chunks, results):
            r_topk = msg.response.search.result.add()
            for (_doc_id, _offset), _score, *args in all_topks:
                r = r_topk.add()
                r.chunk.doc_id = _doc_id
                r.chunk.offset_1d = _offset
                r.score = _score
                # if args is not empty, then it must come from a multiheadindexer
                if args:
                    r.chunk.CopyFrom(args[0])
        send_message(out, msg, self.args.timeout)
