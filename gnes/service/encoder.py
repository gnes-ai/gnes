import zmq

from . import BaseService as BS, Message, send_message
from ..document import MultiSentDocument, get_all_sentences
from ..encoder import PipelineEncoder


class EncoderService(BS):
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

    @BS.handler.register(Message.typ_train)
    def _handler_train(self, msg: 'Message', out: 'zmq.Socket'):
        sents, sent_ids = get_all_sentences(MultiSentDocument.from_list(msg.msg_content))
        self.encoder.train(sents)
        self.encoder.dump(self.args.model_dump)
