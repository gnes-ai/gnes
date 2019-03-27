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
            self.logger.info('uninitialized an encoder built from YAML, need training')

    @BS.handler.register(Message.typ_default)
    def _handler_default(self, msg: 'Message', out: 'zmq.Socket'):
        doc_batch = MultiSentDocument.from_list(msg.msg_content)
        sents, sent_ids = get_all_sentences(doc_batch)
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
