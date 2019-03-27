import zmq

from . import BaseService as BS, Message, send_message
from ..document import MultiSentDocument, get_all_sentences
from ..encoder import PipelineEncoder


class IndexerService(BS):
    def _post_init(self):
        if self.args.model_path:
            # trained, load binary dump
            self.encoder = PipelineEncoder.load(self.args.model_dump)
            self.logger.info('load a trained encoder')
        elif self.args.yaml_path:
            self.encoder = PipelineEncoder.load_yaml(self.args.yaml_path)
            self.logger.info('initialized an encoder from YAML: empty weights, training is needed')

    @BS.handler.register(Message.typ_default)
    def _handler_default(self, msg: 'Message', out: 'zmq.Socket'):
        sents, sent_ids = get_all_sentences(MultiSentDocument.from_list(msg.msg_content))
        vecs = self.encoder.encode(sents)
        send_message(out, msg.copy_mod(msg_content=vecs))
        send_message(out, msg.copy_mod(msg_content=sent_ids, msg_type='SENT_ID_MAP'))

    @BS.handler.register('SENT_ID_MAP')
    def _handler_sent_id(self, msg: 'Message', out: 'zmq.Socket'):
        pass

    @BS.handler.register('DOC_ID_MAP')
    def _handler_doc_id(self, msg: 'Message', out: 'zmq.Socket'):
        pass
