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

from .base import BaseService as BS, ComponentNotLoad, ServiceMode, ServiceError, MessageHandler
from ..document import MultiSentDocument, DocumentMapper, UniSentDocument
from ..messaging import *
from ..proto import gnes_pb2, array2blob, blob2array


class EncoderService(BS):
    handler = MessageHandler(BS.handler)

    def _post_init(self):
        from ..encoder.base import PipelineEncoder

        self._model = None
        try:
            self._model = PipelineEncoder.load(self.args.dump_path)
            self.logger.info('load a trained encoder')
        except FileNotFoundError:
            if self.args.mode == ServiceMode.TRAIN:
                try:
                    self._model = PipelineEncoder.load_yaml(
                        self.args.yaml_path)
                    self.logger.info(
                        'load an uninitialized encoder, training is needed!')
                except FileNotFoundError:
                    raise ComponentNotLoad
            else:
                raise ComponentNotLoad

    def _raise_empty_model_error(self):
        raise ValueError('no model config available, exit!')

    @handler.register(MessageType.DEFAULT.name)
    def _handler_default(self, msg: 'gnes_pb2.Message', out: 'zmq.Socket'):

        chunks = []
        for doc in msg.docs:
            for chunk in doc.chunks:
                if chunk.HasField("text"):
                    chunks.append(chunk.text)
                elif chunk.HasField("blob"):
                    chunks.append(chunk.blob)
                else:
                    raise ValueError("the chunk has empty content")

        if msg.mode == gnes_pb2.Message.TRAIN:
            self._model.train(chunks)
            self.is_model_changed.set()
        elif (msg.mode == gnes_pb2.Message.INDEX) or (
                msg.mode == gnes_pb2.Message.QUERY):
            vecs = self._model.encode(chunks)
            assert len(vecs) == len(chunks)
            i = 0
            for doc in msg.docs:
                for chunk in doc.chunks:
                    chunk.encode.CopyFrom(array2blob(vecs[i]))
            send_message(out, msg, self.args.timeout)
        else:
            raise ServiceError('service %s runs in unknown mode %s' %
                               (self.__class__.__name__, self.args.mode))
