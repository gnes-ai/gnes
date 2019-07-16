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
from typing import List, Union

from .base import BaseService as BS, MessageHandler, BlockMessage
from ..proto import gnes_pb2, array2blob, blob2array


class EncoderService(BS):
    handler = MessageHandler(BS.handler)

    def post_init(self):
        from ..encoder.base import BaseEncoder
        self._model = self.load_model(BaseEncoder)
        self.train_data = []

    @staticmethod
    def get_chunks_from_docs(docs: Union[List['gnes_pb2.Document'], 'gnes_pb2.Document']) -> List:
        if getattr(docs, 'doc_type', None) is not None:
            docs = [docs]
        return [c.text if d.doc_type == gnes_pb2.Document.TEXT else blob2array(c.blob)
                for d in docs for c in d.chunks]

    @handler.register(gnes_pb2.Request.IndexRequest)
    def _handler_index(self, msg: 'gnes_pb2.Message'):
        chunks = self.get_chunks_from_docs(msg.request.index.docs)
        vecs = self._model.encode(chunks)
        s = 0
        for d in msg.request.index.docs:
            d.chunk_embeddings.CopyFrom(array2blob(vecs[s:(s + len(d.chunks))]))
            s += len(d.chunks)

    @handler.register(gnes_pb2.Request.TrainRequest)
    def _handler_train(self, msg: 'gnes_pb2.Message'):
        if msg.request.train.docs:
            chunks = self.get_chunks_from_docs(msg.request.train.docs)
            self.train_data.extend(chunks)
            msg.response.train.status = gnes_pb2.Response.PENDING
            # raise BlockMessage
        if msg.request.train.flush:
            self._model.train(self.train_data)
            self.logger.info('%d samples is flushed for training' % len(self.train_data))
            self.is_model_changed.set()
            self.train_data.clear()
            msg.response.control.status = gnes_pb2.Response.SUCCESS

    @handler.register(gnes_pb2.Request.QueryRequest)
    def _handler_search(self, msg: 'gnes_pb2.Message'):
        chunks = self.get_chunks_from_docs(msg.request.search.query)
        vecs = self._model.encode(chunks)
        msg.request.search.query.chunk_embeddings.CopyFrom(array2blob(vecs))
