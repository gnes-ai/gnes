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

# pylint: disable=low-comment-ratio, missing-license

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

import zmq

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
                    self._model = MultiheadIndexer.load_yaml(self.args.yaml_path)
                    self.logger.info('load an uninitialized indexer, indexing is needed!')
                except FileNotFoundError:
                    raise ComponentNotLoad
            else:
                raise ComponentNotLoad

    def _index_and_notify(self, msg: 'Message', out: 'zmq.Socket', head_name: str):
        res = msg.msg_content
        self._model.add(res[1], res[0], head_name='binary_indexer')
        self._model.add(*res[2], head_name='sent_doc_indexer')
        self._model.add(*res[3], head_name='doc_content_indexer')
        send_message(out, msg.copy_mod(msg_content=head_name), self.args.timeout)
        self.is_model_changed.set()

    @handler.register(Message.typ_default)
    def _handler_default(self, msg: 'Message', out: 'zmq.Socket'):
        if self.args.mode == ServiceMode.INDEX:
            self._index_and_notify(msg, out, 'binary_indexer')
        elif self.args.mode == ServiceMode.QUERY:
            result = self._model.query(msg.msg_content, top_k=self.args.top_k)
            send_message(out, msg.copy_mod(msg_content=result), self.args.timeout)
        else:
            raise ServiceError('service %s runs in unknown mode %s' % (self.__class__.__name__, self.args.mode))

    # @handler.register(Message.typ_sent_id)
    # def _handler_sent_id(self, msg: 'Message', out: 'zmq.Socket'):
    #     self._index_and_notify(msg, out, 'sent_doc_indexer')

    # @handler.register(Message.typ_doc_id)
    # def _handler_doc_id(self, msg: 'Message', out: 'zmq.Socket'):
    #     self._index_and_notify(msg, out, 'doc_content_indexer')
