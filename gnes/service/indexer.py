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

import zmq
import numpy as np

from gnes.proto import gnes_pb2, blob2array
from .base import BaseService as BS, ComponentNotLoad, ServiceMode, ServiceError, MessageHandler
from ..messaging import *


class IndexerService(BS):
    handler = MessageHandler(BS.handler)

    def _post_init(self):
        from ..indexer.base import MultiheadIndexer

        self._model = None
        try:
            self._model = MultiheadIndexer.load(self.args.dump_path)
            self.logger.info('load an indexer')
        except FileNotFoundError:
            if self.args.mode == ServiceMode.INDEX:
                try:
                    self._model = MultiheadIndexer.load_yaml(
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

        doc_ids = []
        offsets = []
        all_vecs = []
        doc_ids = []
        for doc in msg.docs:
            assert doc.doc_size == doc.encodes.shape[0]
            all_vecs.append(blob2array(doc.encodes))
            doc_ids += [doc.id] * doc.doc_size
            offsets += list(range(doc.doc_size))

        self._model.add(zip(doc_ids, offsets),
                        np.concatenate(all_vecs, 0), head_name='binary_indexer')
        self._model.add([d.id for d in msg.docs],
                        [d for d in msg.docs], head_name='doc_indexer')
        send_message(out, msg, self.args.timeout)
        self.is_model_changed.set()

    @handler.register(MessageType.DEFAULT.name)
    def _handler_default(self, msg: 'gnes_pb2.Message', out: 'zmq.Socket'):
        if msg.mode == gnes_pb2.Message.INDEX:
            self._index_and_notify(msg, out)
        elif msg.mode == gnes_pb2.Message.QUERY:
            if not msg.is_encoded:
                raise RuntimeError("the documents should be encoded at first!")

            vecs = blob2array(msg.docs[0].encodes)
            assert len(vecs) == len(msg.querys)

            results = self._model.query(vecs, top_k=msg.querys[0].top_k)

            # convert to protobuf result
            for query, top_k in zip(msg.querys, results):
                for item, score in top_k:
                    r = query.results.add()
                    r.doc_id = item['doc_id']
                    r.doc_size = item['doc_size']
                    r.offset = item['offset']
                    r.score = item['score']
                    r.chunk.offset = item['offset']
                    r.chunk.doc_id = item['doc_id']
                    if msg.doc_type == gnes_pb2.Document.TEXT_DOC:
                        r.chunk.text = item['chunk']
                    elif msg.doc_type == gnes_pb2.Document.IMAGE_DOC:
                        r.chunk.blob = item['chunk']
                    else:
                        raise NotImplemented()
            send_message(out, msg, self.args.timeout)
        else:
            raise ServiceError('service %s runs in unknown mode %s' %
                               (self.__class__.__name__, msg.mode))
