from typing import List

import numpy as np
from bert_serving.client import BertClient
from bert_serving.server import BertServer, get_args_parser

from .base import BaseEncoder, CompositionalEncoder
from ..helper import batching, countdown


class BertEncoder(BaseEncoder):
    store_args_kwargs = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bc_encoder = BertClient(*args, **kwargs)
        self.is_trained = True
        self._bc_encoder_args = args
        self._bc_encoder_kwargs = kwargs

    @batching
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        return self.bc_encoder.encode(text, *args, **kwargs)  # type: np.ndarray

    def __getstate__(self):
        d = super().__getstate__()
        del d['bc_encoder']
        return d

    def __setstate__(self, d):
        super().__setstate__(d)
        self.bc_encoder = BertClient(*self._bc_encoder_args, **self._bc_encoder_kwargs)

    def close(self):
        self.bc_encoder.close()


class BertEncoderWithServer(CompositionalEncoder):
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        return self.component['bert_client'].encode(text, *args, **kwargs)


class BertEncoderServer(BaseEncoder):
    store_args_kwargs = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bert_args = ['-%s' % v for v in args]
        for k, v in kwargs.items():
            bert_args.append('-%s' % k)
            bert_args.append(str(v))

        self._bert_args = get_args_parser().parse_args(bert_args)
        self.is_trained = True
        self._start_bert_server()

    def _start_bert_server(self):
        self.bert_server = BertServer(self._bert_args)
        self.bert_server.start()
        countdown(20, self.logger, 'im blocking this until bert-server is ready')

    def __getstate__(self):
        d = super().__getstate__()
        del d['bert_server']
        return d

    def __setstate__(self, d):
        super().__setstate__(d)
        self._start_bert_server()

    def close(self):
        self.bert_server.close()
