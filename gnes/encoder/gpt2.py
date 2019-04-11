from typing import List

import numpy as np

import torch
from pytorch_pretrained_bert import GPT2Model, GPT2Tokenizer

from .base import BaseEncoder
from ..helper import batching


class GPT2Encoder(BaseEncoder):

    def __init__(self,
                 model_dir: str,
                 use_cuda: bool = None,
                 pooling_strategy: str = 'REDUCE_MEAN',
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

        self.model_dir = model_dir

        # Load pre-trained model tokenizer (vocabulary)
        self._tokenizer = GPT2Tokenizer.from_pretrained(model_dir)

        # Load pre-trained model (weights)
        self._model = GPT2Model.from_pretrained(model_dir)
        self._model.eval()

        self._use_cuda = (use_cuda is not True) and torch.cuda.is_available()

        if self._use_cuda:
            self._model.to('cuda')

        self.pooling_strategy = pooling_strategy

        self.is_trained = True

    @batching
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        batch_size = len(text)

        # tokenize text
        tokens_ids = []
        tokens_lens = []
        max_len = 0
        for _ in text:
            token_ids = self._tokenizer.encode(_)
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
        masks_tensor = torch.arange(max_len)[None, :] < tokens_lens[:, None]
        masks_tensor = masks_tensor.to(
            masks_tensor.device, dtype=torch.float32)

        if self._use_cuda:
            # If you have a GPU, put everything on cuda
            tokens_tensor = tokens_tensor.to('cuda')
            tokens_lens = tokens_lens.to('cuda')
            masks_tensor = masks_tensor.to('cuda')

        # Predict hidden states features for each layer
        with torch.no_grad():
            # the encoded-hidden-states at the top of the model, as a
            # torch.FloatTensor of size [batch_size, sequence_length, hidden_size]
            output_tensor, _ = self._model(tokens_tensor)
            output_dim = output_tensor.shape[2]

            tiled_masks = masks_tensor.unsqueeze(2).repeat(1, 1, output_dim)

            output_tensor = torch.mul(tiled_masks, output_tensor)

            minus_mask = lambda x, m: x - (1.0 - m).unsqueeze(2) * 1e30
            mul_mask = lambda x, m: torch.mul(x, m.unsqueeze(2))

            masked_reduce_mean = lambda x, m : torch.div(torch.sum(mul_mask(x, m), dim=1), torch.sum(m.unsqueeze(2), dim=1) + 1e-10)
            masked_reduce_max = lambda x, m: torch.max(minus_mask(x, m), 1)[0]

            if self.pooling_strategy == 'REDUCE_MEAN':
                # sumed_tensor = torch.sum(output_tensor, dim=1)
                # output_tensor = torch.div(
                #     sumed_tensor,
                #     tokens_lens.unsqueeze(1).repeat(1, output_dim).to(
                #         tokens_lens.device, dtype=torch.float32))
                output_tensor = masked_reduce_mean(output_tensor, masks_tensor)
            elif self.pooling_strategy == 'REDUCE_MAX':
                # minus_output = output_tensor - (1.0 - tiled_masks) * 1e30
                # output_tensor, _ = torch.max(minus_output, 1)
                output_tensor = masked_reduce_max(output_tensor, masks_tensor)
            elif self.pooling_strategy == 'REDUCE_MEAN_MAX':
                output_tensor = torch.cat(
                    (masked_reduce_mean(output_tensor, masks_tensor),
                     masked_reduce_max(output_tensor, masks_tensor)),
                    dim=1)
            else:
                raise ValueError(
                    'pooling_strategy: %s has not been implemented' %
                    self.pooling_strategy)

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
        self._tokenizer = GPT2Tokenizer.from_pretrained(self.model_dir)
        self._model = GPT2Model.from_pretrained(self.model_dir)
        self._model.eval()

        self._use_cuda = (self._use_cuda is
                          not False) and torch.cuda.is_available()
        if self._use_cuda:
            self._model.to('cuda')
