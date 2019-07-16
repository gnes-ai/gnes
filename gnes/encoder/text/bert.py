#  Tencent is pleased to support the open source community by making GNES available.
#
#  Copyright (C) 2019 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# pylint: disable=low-comment-ratio


from typing import List

import numpy as np

from ..base import CompositionalEncoder, BaseTextEncoder
from ...helper import batching


class BertEncoder(BaseTextEncoder):
    store_args_kwargs = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_trained = True
        self._bc_encoder_args = args
        self._bc_encoder_kwargs = kwargs

    def post_init(self):
        from bert_serving.client import BertClient
        self.bc_encoder = BertClient(*self._bc_encoder_args, **self._bc_encoder_kwargs)

    @batching
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        return self.bc_encoder.encode(text, *args, **kwargs)  # type: np.ndarray

    def close(self):
        self.bc_encoder.close()


class BertEncoderWithServer(CompositionalEncoder):
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        return self.component['bert_client'].encode(text, *args, **kwargs)


class BertEncoderServer(BaseTextEncoder):
    store_args_kwargs = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bert_args = ['-%s' % v for v in args]
        for k, v in kwargs.items():
            bert_args.append('-%s' % k)
            bert_args.append(str(v))
        self._bert_args = bert_args
        self.is_trained = True

    def post_init(self):
        from bert_serving.server import BertServer
        from bert_serving.server import get_args_parser
        self.bert_server = BertServer(get_args_parser().parse_args(self._bert_args))
        self.bert_server.start()
        self.bert_server.is_ready.wait()

    def close(self):
        self.bert_server.close()
