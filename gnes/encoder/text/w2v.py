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
from ...helper import batching, pooling_simple


class Word2VecEncoder(BaseTextEncoder):
    def __init__(self, model_dir,
                 skiprows: int = 1,
                 batch_size: int = 64,
                 dimension: int = 300,
                 pooling_strategy: str = 'REDUCE_MEAN', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_dir = model_dir
        self.skiprows = skiprows
        self.batch_size = batch_size
        self.pooling_strategy = pooling_strategy
        self.is_trained = True
        self.dimension = dimension

    def post_init(self):
        from ...helper import Tokenizer
        count = 0
        self.word2vec_df = {}
        with open(self.model_dir, 'r') as f:
            for line in f.readlines():
                line = line.strip().split(' ')
                if count < self.skiprows:
                    count += 1
                    continue
                if len(line) > self.dimension:
                    self.word2vec_df[line[0]] = np.array([float(i) for i in line[1:]], dtype=np.float32)

        self.empty = np.zeros([self.dimension], dtype=np.float32)
        self.cn_tokenizer = Tokenizer()

    @batching
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        # tokenize text
        batch_tokens = [self.cn_tokenizer.tokenize(sent) for sent in text]
        pooled_data = []

        for tokens in batch_tokens:
            _layer_data = [self.word2vec_df.get(token, self.empty) for token in tokens]
            pooled_data.append(pooling_simple(_layer_data, self.pooling_strategy))

        return np.array(pooled_data).astype(np.float32)

