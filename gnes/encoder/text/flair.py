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


from typing import List

import numpy as np

from ..base import BaseTextEncoder
from ...helper import batching, pooling_np


class FlairEncoder(BaseTextEncoder):
    is_trained = True

    def __init__(self, model_name: str = 'multi-forward-fast',
                 pooling_strategy: str = 'REDUCE_MEAN', *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model_name = model_name
        self.pooling_strategy = pooling_strategy

    def post_init(self):
        from flair.embeddings import FlairEmbeddings
        self._flair = FlairEmbeddings(self.model_name)

    @batching
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        from flair.data import Sentence
        # tokenize text
        batch_tokens = [Sentence(sent) for sent in text]

        flair_encodes = self._flair.embed(batch_tokens)

        pooled_data = []
        for sentence in flair_encodes:
            _layer_data = np.stack([s.embedding.numpy() for s in sentence])
            _pooled = pooling_np(_layer_data, self.pooling_strategy)
            pooled_data.append(_pooled)
        return np.array(pooled_data, dtype=np.float32)
