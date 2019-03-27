import zmq

from . import BaseService, Message, send_message
from ..document import MultiSentDocument, get_all_sentences
from ..encoder import PipelineEncoder


class EncoderService(BaseService):
    def _post_init(self):
        if self.args.model_path:
            # trained, load binary dump
            self.encoder = PipelineEncoder.load(self.args.model_dump)
        elif self.args.yaml_path:
            self.encoder = PipelineEncoder.load_yaml(self.args.yaml_path)

    def _handler_default(self, msg: 'Message', out: 'zmq.Socket'):
        sents, sent_ids = get_all_sentences(MultiSentDocument.from_list(msg.msg_content))
        vecs = self.encoder.encode(sents)
        send_message(out, msg.copy_mod(msg_content=vecs))
