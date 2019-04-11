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
            if self.args.mode == ServiceMode.ADD:
                try:
                    self._model = MultiheadIndexer.load_yaml(self.args.yaml_path)
                    self.logger.info('load an uninitialized indexer, indexing is needed!')
                except FileNotFoundError:
                    raise ComponentNotLoad
            else:
                raise ComponentNotLoad

    @handler.register(Message.typ_default)
    def _handler_default(self, msg: 'Message', out: 'zmq.Socket'):
        if self.args.mode == ServiceMode.ADD:
            self._model.add(*msg.msg_content, head_name='binary_indexer')
            self.is_model_changed.set()
        elif self.args.mode == ServiceMode.QUERY:
            result = self._model.query(msg.msg_content, top_k=self.args.top_k)
            send_message(out, msg.copy_mod(msg_content=result), self.args.timeout)
        else:
            raise ServiceError('service %s runs in unknown mode %s' % (self.__class__.__name__, self.args.mode))

    @handler.register(Message.typ_sent_id)
    def _handler_sent_id(self, msg: 'Message', out: 'zmq.Socket'):
        self._model.add(*msg.msg_content, head_name='sent_doc_indexer')
        self.is_model_changed.set()

    @handler.register(Message.typ_doc_id)
    def _handler_doc_id(self, msg: 'Message', out: 'zmq.Socket'):
        self._model.add(*msg.msg_content, head_name='doc_content_indexer')
        self.is_model_changed.set()
