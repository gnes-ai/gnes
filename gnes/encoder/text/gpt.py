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
# noinspection PyUnresolvedReferences

from typing import List

import numpy as np

from ..base import BaseTextEncoder
from ...helper import batching, pooling_torch


class GPTEncoder(BaseTextEncoder):
    def __init__(self,
                 model_dir: str,
                 batch_size: int = 64,
                 use_cuda: bool = False,
                 pooling_strategy: str = 'REDUCE_MEAN',
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

        self.model_dir = model_dir
        self.batch_size = batch_size
        self.pooling_strategy = pooling_strategy
        self._use_cuda = use_cuda
        self.is_trained = True

    def post_init(self):
        import torch
        # Load pre-trained model tokenizer (vocabulary)
        self._init_model_tokenizer()
        self._use_cuda = self._use_cuda and torch.cuda.is_available()
        if self._use_cuda: self._model.to('cuda')

    def _get_token_ids(self, x):
        return self._tokenizer.convert_tokens_to_ids(self._tokenizer.tokenize(x))

    def _get_output_tensor(self, x):
        return self._model(x)

    def _init_model_tokenizer(self):
        from pytorch_pretrained_bert import OpenAIGPTTokenizer, OpenAIGPTModel
        self._tokenizer = OpenAIGPTTokenizer.from_pretrained(self.model_dir)
        self._model = OpenAIGPTModel.from_pretrained(self.model_dir)
        self._model.eval()

    @batching
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        import torch
        batch_size = len(text)

        # tokenize text
        tokens_ids = []
        tokens_lens = []
        max_len = 0
        for _ in text:
            # Convert token to vocabulary indices
            token_ids = self._get_token_ids(_)
            token_len = len(token_ids)

            if max_len < token_len:
                max_len = token_len

            tokens_ids.append(token_ids)
            tokens_lens.append(token_len)

        batch_data = np.zeros([batch_size, max_len], dtype=np.int64)
        # batch_mask = np.zeros([batch_size, max_len], dtype=np.float32)
        for i, ids in enumerate(tokens_ids):
            batch_data[i, :tokens_lens[i]] = tokens_ids[i]
            # batch_mask[i, :tokens_lens[i]] = 1

        # Convert inputs to PyTorch tensors
        tokens_tensor = torch.tensor(batch_data)
        tokens_lens = torch.LongTensor(tokens_lens)
        mask_tensor = torch.arange(max_len)[None, :] < tokens_lens[:, None]
        mask_tensor = mask_tensor.to(
            mask_tensor.device, dtype=torch.float32)

        if self._use_cuda:
            # If you have a GPU, put everything on cuda
            tokens_tensor = tokens_tensor.to('cuda')
            mask_tensor = mask_tensor.to('cuda')

        # Predict hidden states features for each layer
        with torch.no_grad():
            # the encoded-hidden-states at the top of the model, as a
            # torch.FloatTensor of size [batch_size, sequence_length, hidden_size]
            output_tensor = self._get_output_tensor(tokens_tensor)
            output_tensor = pooling_torch(output_tensor, mask_tensor, self.pooling_strategy)

        if self._use_cuda:
            output_tensor = output_tensor.cpu()
        return output_tensor.numpy()



class GPT2Encoder(GPTEncoder):

    def _get_token_ids(self, x):
        return self._tokenizer.encode(x)

    def _get_output_tensor(self, x):
        return self._model(x)[0]

    def _init_model_tokenizer(self):
        from pytorch_pretrained_bert import GPT2Model, GPT2Tokenizer
        self._tokenizer = GPT2Tokenizer.from_pretrained(self.model_dir)
        self._model = GPT2Model.from_pretrained(self.model_dir)
        self._model.eval()
