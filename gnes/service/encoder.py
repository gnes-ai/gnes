import zmq

from .base import BaseService as BS, Message, ComponentNotLoad, send_message, ServiceMode, ServiceError
from ..document import MultiSentDocument, DocumentMapper
from ..encoder import PipelineEncoder


class EncoderService(BS):
    def _post_init(self):
        self.encoder = None
        try:
            self.encoder = PipelineEncoder.load(self.args.dump_path)
            self.logger.info('load a trained encoder')
        except FileNotFoundError:
            if self.args.mode == ServiceMode.TRAIN:
                try:
                    self.encoder = PipelineEncoder.load_yaml(self.args.yaml_path)
                    self.logger.info('load an uninitialized encoder, training is needed!')
                except FileNotFoundError:
                    raise ComponentNotLoad
            else:
                raise ComponentNotLoad

    def _raise_empty_model_error(self):
        raise ValueError('no model config available, exit!')

    @BS.handler.register(Message.typ_default)
    def _handler_default(self, msg: 'Message', out: 'zmq.Socket'):
        doc_mapper = DocumentMapper(MultiSentDocument.from_list(msg.msg_content))
        sents, sent_ids = doc_mapper.sent_id_sentence
        if not sents:
            raise ServiceError('received an empty list, nothing to do')
        if self.args.mode == ServiceMode.TRAIN:
            self.encoder.train(sents)
            self.encoder.dump(self.args.dump_path)
        elif self.args.mode == ServiceMode.ADD:
            vecs = self.encoder.encode(sents)
            send_message(out, msg.copy_mod(msg_content=(sent_ids, vecs)), self.args.timeout)
            send_message(out, msg.copy_mod(msg_content=doc_mapper.sent_id_doc_id, msg_type='SENT_ID_MAP'),
                         self.args.timeout)
            send_message(out, msg.copy_mod(msg_content=doc_mapper.doc_id_document, msg_type='SENT_ID_MAP'),
                         self.args.timeout)
        elif self.args.mode == ServiceMode.QUERY:
            vecs = self.encoder.encode(sents)
            send_message(out, msg.copy_mod(msg_content=vecs), self.args.timeout)
        else:
            raise ServiceError('unknown service mode: %s' % self.args.mode)

    def close(self):
        if self.encoder:
            self.encoder.close()
        super().close()
