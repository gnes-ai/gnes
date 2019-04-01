import zmq

from . import BaseService as BS, Message, ComponentNotLoad, send_message
from ..document import MultiSentDocument, DocumentMapper
from ..encoder import PipelineEncoder


class EncoderService(BS):
    def _post_init(self):
        self.encoder = None
        try:
            self.encoder = PipelineEncoder.load(self.args.model_path)
            self.logger.info('load a trained encoder')
        except FileNotFoundError:
            if self.args.train:
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
            self.logger.error('received an empty list, nothing to do')
            return
        if self.args.train:
            self.encoder.train(sents)
            self.encoder.dump(self.args.model_path)
        else:
            vecs = self.encoder.encode(sents)
            send_message(out, msg.copy_mod(msg_content=(sent_ids, vecs)), self.args.timeout)
            send_message(out, msg.copy_mod(msg_content=doc_mapper.sent_id_doc_id, msg_type='SENT_ID_MAP'),
                         self.args.timeout)
            send_message(out, msg.copy_mod(msg_content=doc_mapper.doc_id_document, msg_type='SENT_ID_MAP'),
                         self.args.timeout)
            # # QUERY
            # # encode -> vecs
            # # binary indexer: vecs -> sent_id  SCORE
            # # s-leveldb: sent_id -> doc_id  SCORE
            # # d-leveldb: doc_id -> content   1-to-1
            self.logger.info('done!')
        # block wait until

    def close(self):
        if self.encoder:
            self.encoder.close()
        super().close()
