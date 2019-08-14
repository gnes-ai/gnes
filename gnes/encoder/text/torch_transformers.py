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
from ...helper import batching


class TorchTransformersEncoder(BaseTextEncoder):
    is_trained = True

    def __init__(self, model_dir: str,
                 model_name: str,
                 tokenizer_name: str,
                 use_cuda: bool = False,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_dir = model_dir
        self.model_name = model_name
        self.tokenizer_name = tokenizer_name
        self.use_cuda = use_cuda

    def post_init(self):
        import pytorch_transformers as ptt

        self.tokenizer = getattr(ptt, self.tokenizer_name).from_pretrained(self.model_dir)
        self.model = getattr(ptt, self.model_name).from_pretrained(self.model_dir)

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
            token_ids = self.tokenizer.encode(_)
            token_len = len(token_ids)

            if max_len < token_len:
                max_len = token_len

            tokens_ids.append(token_ids)
            tokens_lens.append(token_len)

        batch_data = np.zeros([batch_size, max_len], dtype=np.int64)
        # batch_mask = np.zeros([batch_size, max_len], dtype=np.float32)
        for i, ids in enumerate(tokens_ids):
            batch_data[i, :tokens_lens[i]] = ids
            # batch_mask[i, :tokens_lens[i]] = 1

        # Convert inputs to PyTorch tensors
        tokens_tensor = torch.tensor(batch_data)
        tokens_lens = torch.LongTensor(tokens_lens)
        mask_tensor = torch.arange(max_len)[None, :] < tokens_lens[:, None]
        mask_tensor = mask_tensor.to(
            mask_tensor.device, dtype=torch.float32)

        if self.use_cuda:
            # If you have a GPU, put everything on cuda
            tokens_tensor = tokens_tensor.to('cuda')
            mask_tensor = mask_tensor.to('cuda')

        with torch.no_grad():
            out_tensor = self.model(tokens_tensor)[0]
            out_tensor = torch.mul(out_tensor, mask_tensor.unsqueeze(2))
            if self.use_cuda:
                out_tensor = out_tensor.cpu()

        return out_tensor.numpy()
