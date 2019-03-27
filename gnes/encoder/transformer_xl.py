'''
from typing import List

import numpy as np

from .base import BaseEncoder, CompositionalEncoder
from ..helper import batching, countdown
from pytorch_pretrained_bert import TransfoXLTokenizer, TransfoXLModel


class TransformerEncoder(BaseEncoder):

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
'''
import os
os.environ['CUDA_VISIBLE_DEVICES'] = u'2'
import torch
from pytorch_pretrained_bert import TransfoXLTokenizer, TransfoXLModel, TransfoXLLMHeadModel
import os

# OPTIONAL: if you want to have more information on what's happening, activate the logger as follows
model_dir = '/data1/cips/data/transformer-xl/'

# Load pre-trained model tokenizer (vocabulary from wikitext 103)
tokenizer = TransfoXLTokenizer.from_pretrained(model_dir)
model = TransfoXLModel.from_pretrained(model_dir)
model.eval()
model.to('cuda')
import time

stime = time.time()


# Tokenized input

res = []
for _ in range(100):
    text_1 = "Who was Jim Henson ?"

    tokenized_text_1 = tokenizer.tokenize(text_1)

    # Convert token to vocabulary indices
    indexed_tokens_1 = tokenizer.convert_tokens_to_ids(tokenized_text_1)
    res.append(indexed_tokens_1)

# Convert inputs to PyTorch tensors
tokens_tensor_1 = torch.tensor(res)


# If you have a GPU, put everything on cuda
tokens_tensor_1 = tokens_tensor_1.to('cuda')



with torch.no_grad():
    # Predict hidden states features for each layer
    hidden_states_1, mems_1 = model(tokens_tensor_1)

print(time.time() - stime)