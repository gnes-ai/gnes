from typing import List

import numpy as np
import torch
from pytorch_pretrained_bert import OpenAIGPTTokenizer, OpenAIGPTModel

from .base import BaseEncoder
from ..helper import batching, pooling_torch


class GPTEncoder(BaseEncoder):

    def __init__(self,
                 model_path: str,
                 batch_size: int = 64,
                 use_cuda: bool = False,
                 pooling_strategy: str = 'REDUCE_MEAN',
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

        self.model_path = model_path
        self.batch_size = batch_size

        # Load pre-trained model tokenizer (vocabulary)
        self._init_model_tokenizer()

        self._use_cuda = use_cuda and torch.cuda.is_available()

        if self._use_cuda:
            self._model.to('cuda')

        self.pooling_strategy = pooling_strategy

        self.is_trained = True

    def _get_token_ids(self, x):
        return self._tokenizer.convert_tokens_to_ids(self._tokenizer.tokenize(x))

    def _get_output_tensor(self, x):
        return self._model(x)

    def _init_model_tokenizer(self):
        self._tokenizer = OpenAIGPTTokenizer.from_pretrained(self.model_path)
        self._model = OpenAIGPTModel.from_pretrained(self.model_path)
        self._model.eval()

    @batching
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
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

    def __getstate__(self):
        d = super().__getstate__()
        del d['_tokenizer']
        del d['_model']
        return d

    def __setstate__(self, d):
        super().__setstate__(d)
        self._init_model_tokenizer()
        self._use_cuda = self._use_cuda and torch.cuda.is_available()
        if self._use_cuda: self._model.to('cuda')
