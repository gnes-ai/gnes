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


from typing import List, Union

from .base import BaseService as BS, MessageHandler
from ..proto import gnes_pb2, array2blob, blob2array


class EncoderService(BS):
    handler = MessageHandler(BS.handler)

    def post_init(self):
        from ..encoder.base import BaseEncoder
        self._model = self.load_model(BaseEncoder)
        self.train_data = []

    def embed_chunks_in_docs(self, docs: Union[List['gnes_pb2.Document'], 'gnes_pb2.Document'],
                             do_encoding: bool = True,
                             is_input_list: bool = True):
        if not is_input_list:
            docs = [docs]

        contents = []
        chunks = []

        for d in docs:
            if not d.chunks:
                self.logger.warning('document (doc_id=%s) contains no chunks!' % d.doc_id)
                continue

            for c in d.chunks:
                if d.doc_type == gnes_pb2.Document.TEXT:
                    contents.append(c.text)
                elif d.doc_type in {gnes_pb2.Document.IMAGE, gnes_pb2.Document.VIDEO}:
                    contents.append(blob2array(c.blob))
                else:
                    self.logger.warning(
                        'chunk content is in type: %s, dont kow how to handle that, ignored' % c.WhichOneof('content'))
                chunks.append(c)

        if do_encoding and contents:
            try:
                embeds = self._model.encode(contents)
                if len(chunks) != embeds.shape[0]:
                    self.logger.error(
                        'mismatched %d chunks and a %s shape embedding, '
                        'the first dimension must be the same' % (len(chunks), embeds.shape))
                for idx, c in enumerate(chunks):
                    c.embedding.CopyFrom(array2blob(embeds[idx]))
            except Exception as ex:
                self.logger.error(ex, exc_info=True)
                self.logger.warning('encoder service throws an exception, '
                                    'the sequel pipeline may not work properly')

        return contents

    @handler.register(gnes_pb2.Request.IndexRequest)
    def _handler_index(self, msg: 'gnes_pb2.Message'):
        self.embed_chunks_in_docs(msg.request.index.docs)

    @handler.register(gnes_pb2.Request.TrainRequest)
    def _handler_train(self, msg: 'gnes_pb2.Message'):
        if msg.request.train.docs:
            contents = self.embed_chunks_in_docs(msg.request.train.docs, do_encoding=False)
            self.train_data.extend(contents)
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
        self.embed_chunks_in_docs(msg.request.search.query, is_input_list=False)

    @handler.register_hook(hook_type=('pre', 'post'), only_when_verbose=True)
    def _hook_debug_msg(self, msg: 'gnes_pb2.Message', *args, **kwargs):
        from pprint import pformat

        debug_kv = {
            'envelope': lambda: msg.envelope,
            'num_docs': lambda: len(msg.request.index.docs),
            'num_chunks in doc[0]': lambda: len(msg.request.index.docs[0].chunks),
            'docs[0].chunks[0].content_type': lambda: msg.request.index.docs[0].chunks[0].WhichOneof('content'),
            'docs[0].chunks[0].weight': lambda: msg.request.index.docs[0].chunks[0].weight,
            'docs[0].chunks[0].embedding': lambda: blob2array(msg.request.index.docs[0].chunks[0].embedding),
            'docs[0].chunks[0].embedding[0]': lambda: blob2array(msg.request.index.docs[0].chunks[0].embedding)[0]
        }
        debug_info = {}
        for k, v in debug_kv.items():
            try:
                r = v()
            except Exception as ex:
                r = 'fail to get the value, reason: %s' % ex
            debug_info[k] = r
        self.logger.info(pformat(debug_info))
