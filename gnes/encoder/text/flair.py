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
from ...helper import batching, as_numpy_array


class FlairEncoder(BaseTextEncoder):
    is_trained = True

    def __init__(self, pooling_strategy: str = 'mean', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pooling_strategy = pooling_strategy

    def post_init(self):
        from flair.embeddings import DocumentPoolEmbeddings, WordEmbeddings, FlairEmbeddings
        self._flair = DocumentPoolEmbeddings(
            [WordEmbeddings('glove'),
             FlairEmbeddings('news-forward'),
             FlairEmbeddings('news-backward')],
            pooling=self.pooling_strategy)

    @batching
    @as_numpy_array
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        from flair.data import Sentence
        import torch
        # tokenize text
        batch_tokens = [Sentence(v) for v in text]
        self._flair.embed(batch_tokens)
        return torch.stack([v.embedding for v in batch_tokens]).detach()
