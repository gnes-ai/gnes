import zmq

from gnes.indexer.base import CompositionalIndexer
from . import BaseService as BS, Message


class IndexerService(BS):
    def _post_init(self):
        self.indexer = None
        try:
            if self.args.index_path:
                self.indexer = CompositionalIndexer.load(self.args.index_path)
                self.logger.info('load an indexer')
        except FileNotFoundError:
            self.logger.warning('model_path=%s does not exist, will dump to it' % self.args.index_path)
            try:
                if self.args.yaml_path:
                    self.indexer = CompositionalIndexer.load_yaml(self.args.yaml_path)
            except FileNotFoundError:
                self.logger.warning('yaml_path=%s does not exist' % self.args.yaml_path)
                raise ValueError('no model config available, exit!')

    @BS.handler.register(Message.typ_default)
    def _handler_default(self, msg: 'Message', out: 'zmq.Socket'):
        self.indexer.add('binary_indexer', msg.msg_content)

    @BS.handler.register('SENT_ID_MAP')
    def _handler_sent_id(self, msg: 'Message', out: 'zmq.Socket'):
        self.indexer.add('sent_doc_indexer', msg.msg_content)

    @BS.handler.register('DOC_ID_MAP')
    def _handler_doc_id(self, msg: 'Message', out: 'zmq.Socket'):
        self.indexer.add('doc_content_indexer', msg.msg_content)

    def close(self):
        if self.indexer:
            self.indexer.close()
        super().close()
