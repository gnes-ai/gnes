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

from ..base import BaseTextEncoder
from ...helper import batching, pooling_np


class ElmoEncoder(BaseTextEncoder):

    def __init__(self, model_dir: str, batch_size: int = 64, pooling_layer: int = -1,
                 pooling_strategy: str = 'REDUCE_MEAN', *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model_dir = model_dir

        self.batch_size = batch_size
        if pooling_layer > 2:
            raise ValueError('pooling_layer = %d is not supported now!' %
                             pooling_layer)
        self.pooling_layer = pooling_layer
        self.pooling_strategy = pooling_strategy
        self.is_trained = True

    def post_init(self):
        from elmoformanylangs import Embedder
        from ...helper import Tokenizer
        self._elmo = Embedder(model_dir=self.model_dir, batch_size=self.batch_size)
        self.cn_tokenizer = Tokenizer()

    @batching
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        # tokenize text
        batch_tokens = [self.cn_tokenizer.tokenize(sent) for sent in text]

        elmo_encodes = self._elmo.sents2elmo(batch_tokens, output_layer=-2)

        pooled_data = []
        for token_encodes in elmo_encodes:
            if self.pooling_layer == -1:
                _layer_data = np.average(token_encodes, axis=0)
            elif self.pooling_layer >= 0:
                _layer_data = token_encodes[self.pooling_layer]
            else:
                raise ValueError('pooling_layer = %d is not supported now!' %
                                 self.pooling_layer)

            _pooled = pooling_np(_layer_data, self.pooling_strategy)
            pooled_data.append(_pooled)
        return np.array(pooled_data, dtype=np.float32)

