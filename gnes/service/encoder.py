import zmq

from . import BaseService as BS, Message, send_message
from ..document import MultiSentDocument, get_all_sentences
from ..encoder import PipelineEncoder


class EncoderService(BS):
    def _post_init(self):
        self.encoder = None
        if self.args.train:
            self.logger.warning('training is enabled. this encoder wont use output socket')
            try:
                if self.args.model_path:
                    self.encoder = PipelineEncoder.load(self.args.model_path)
                    self.logger.info('load a trained encoder, but it will be override after training')
            except FileNotFoundError:
                self.logger.warning('model_path=%s does not exist, will dump to it' % self.args.model_path)
                try:
                    if self.args.yaml_path:
                        self.encoder = PipelineEncoder.load_yaml(self.args.yaml_path)
                except FileNotFoundError:
                    self.logger.warning('yaml_path=%s does not exist' % self.args.yaml_path)
                    raise ValueError('no model config available, exit!')
        elif self.args.model_path:
            try:
                self.encoder = PipelineEncoder.load(self.args.model_path)
                self.logger.info('load a trained encoder')
            except FileNotFoundError:
                raise ValueError('no model config available, exit!')
        else:
            raise ValueError('no model config available, exit!')

    @BS.handler.register(Message.typ_default)
    def _handler_default(self, msg: 'Message', out: 'zmq.Socket'):
        doc_batch = MultiSentDocument.from_list(msg.msg_content)
        sents, sent_ids = get_all_sentences(doc_batch)
        if not sents:
            self.logger.error('received an empty list, nothing to do')
            return
        if self.args.train:
            self.encoder.train(sents)
            self.encoder.dump(self.args.model_path)
        else:
            vecs = self.encoder.encode(sents)
            # send out a three-part message to out
            # they are syncronized by the msg.req_id
            send_message(out, msg.copy_mod(msg_content=vecs))
            send_message(out, msg.copy_mod(msg_content=sent_ids, msg_type='SENT_ID_MAP'))
            send_message(out, msg.copy_mod(msg_content=doc_batch, msg_type='DOC_ID_MAP'))

    def close(self):
        if self.encoder:
            self.encoder.close()
        super().close()
